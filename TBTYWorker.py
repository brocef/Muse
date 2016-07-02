import threading
from abc import ABCMeta, abstractmethod

WORKER_TYPES = ('SCT', 'CVN', 'DOC', 'AGT', 'FND')
WORKER_TYPE_ORDER = dict(enumerate(WORKER_TYPES))
WORKER_TYPE_MAP = dict((v,k) for k,v in WORKER_TYPE_ORDER.iteritems())

class TBTYWorker(threading.Thread):
    __metaclass__ = ABCMeta
    def __init__(self, config, worker_id, input_q, output_q, progress_callback):
        super(TBTYWorker, self).__init__()
        self.config = config
        self.w_id = worker_id
        self.in_q = input_q
        self.out_q = output_q
        self.prog_cb = progress_callback
        self.P_START = 'Starting task'
        self.P_DONE = 'Task completed'

    @abstractmethod
    def process(self, item, prog_cb):
        raise Exception('Not yet implemented!')

    def getID(self):
        return self.w_id

    def run(self):
        while 1:
            i = self.in_q.get()
            if i == None:
                self.out_q.put(None)
            else:
                self.prog_cb(self.P_START, cur_pct=0.0)
                for out in self.process(i, self.prog_cb):
                    self.out_q.put(out)
                self.prog_cb(self.P_DONE, cur_pct=1.0)
            self.in_q.task_done()
            if i == None:
                break

