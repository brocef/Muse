from __future__ import print_function
import threading
from abc import ABCMeta, abstractmethod
import time
from Queue import Queue

WORKER_TYPES = ('SCT', 'CVN', 'DOC', 'AGT', 'FND')
WORKER_TYPE_ORDER = dict(enumerate(WORKER_TYPES))
WORKER_TYPE_MAP = dict((v,k) for k,v in WORKER_TYPE_ORDER.iteritems())

class worker(threading.Thread):
    __metaclass__ = ABCMeta
    def __init__(self, config, worker_id, input_q, output_q, progress_callback, std_out, std_err):
        super(worker, self).__init__()
        self.config = config
        self.w_id = worker_id
        self.w_num = int(self.w_id[3:])+1
        self.in_q = input_q
        self._buf_q = Queue()
        self.out_q = output_q
        self.prog_cb = lambda status: progress_callback(self.w_id, status, self.estimateProb())
        self.err_cb = lambda status, err: progress_callback(self.w_id, status, err)
        self.P_START = 'Starting task'
        self.P_DONE = 'Task completed'
        self.W_DONE = '-WORKER SHUTDOWN-'
        self._num_proc = 0
        self._num_in = None
        self._saw_none = False
        self._recv_none = False
        self._kill = False
        self.std_out = std_out
        self.std_err = std_err

    def eprint(self, *args, **kwargs):
        print(*args, file=self.std_err, **kwargs)

    def print(self, *args, **kwargs):
        print(*args, file=self.std_out, **kwargs)

    @abstractmethod
    def process(self, item, prog_cb):
        raise Exception('Not yet implemented!')

    def getID(self):
        return self.w_id

    def estimateProb(self):
        if self._kill:
            return ('---%', ('%d items' % self._num_proc) if self._num_proc != 1 else '1 item')
        else:
            if self._num_in == None:
                return min(0.4, float(self._num_proc) / 100.0)
            else:
                return min(1.0, float(self._num_proc) / self._num_in)

    def run(self):
        while 1:
            while not self.in_q.empty():
                elem = self.in_q.get()
                if elem != None:
                    (e, n) = elem
                    self._num_in = n
                    self._buf_q.put(e)
                else:
                    self._buf_q.put(elem)
            if self._buf_q.empty():
                elem = self.in_q.get()
                if elem != None:
                    (e, n) = elem
                    self._num_in = n
                    self._buf_q.put(e)
                else:
                    self._buf_q.put(elem)
            else:
                i = self._buf_q.get()
                if i == None:
                    self.out_q.put(None)
                    self._kill = True
                else:
                    self.prog_cb(self.P_START)
                    try:
                        for out in self.process(i, self.prog_cb):
                            self._num_proc += 1
                            self.out_q.put((out, self._num_proc))
                        self.prog_cb(self.P_DONE)
                    except Exception as e:
                        self.err_cb(str(e), -1.0)
                self.in_q.task_done()
                if self._kill:
                    self.prog_cb(self.W_DONE)
                    break

