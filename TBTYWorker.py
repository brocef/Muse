import threading
import socket
import re
import Queue
from abc import ABCMeta, abstractmethod

COMMANDS = {
        'init': '!INIT!',
        'kill': '!KILL!' 
    }
WORKER_TYPES = ('SCT', 'CVN', 'DOC', 'AGT', 'FRND')
WORKER_TYPE_ORDER = dict(enumerate(WORKER_TYPES))
WORKER_TYPE_MAP = dict((v,k) for k,v in WORKER_TYPE_ORDER.iteritems())

class TBTYWorker(threading.Thread):
    __metaclass__ = ABCMeta
    def __init__(self, config):
        super(TBTYWorker, self).__init__()
        self.config = config
        self.TYPES = WORKER_TYPES
        self._data = ''
        self._ptr = 0
        self.queue = Queue.Queue()
        self.BUF_SIZE = 1024
        self.delimiter = '\n'
        self.initialized = False

    @staticmethod
    def parse_msg(message):
        m = re.match(r'^<([A-Z]+)>(.+)$', message)
        return m.groups() if m is not None else (None, None)

    def send_msg(self, message):
        self.sock.sendall('<%s>%s\n' % (self.w_type, message))

    def recv_msg(self):
        if not self.queue.empty():
            self.last_msg = self.queue.get()
            return True

        while 1:
            newdata = self.recv_sock()
            if not newdata or len(newdata) == 0:
                return False
            self._data += newdata
            while self._ptr < len(self._data):
                if self._data[self._ptr] == self.delimiter:
                    ex_msg = self._data[:self._ptr]
                    self.queue.put(ex_msg)
                    self._data = self._data[self._ptr+1:]
                    self._ptr = 0
                else:
                    self._ptr += 1

            if len(self._data) == 0:
                break

        self.last_msg = self.queue.get()
        return True
        
    
    @abstractmethod
    def process(self, data):
        raise Exception('Cannot process data')

    def init(self, worker_type):
        self.w_type = worker_type
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.config.getServerAddress())
        self.recv_sock = lambda: self.sock.recv(self.BUF_SIZE)
        self.send_msg('init')
        try:
            while self.recv_msg():
                if self.last_msg == COMMANDS['init']:
                    self.initialized = True
                elif self.last_msg == COMMANDS['kill']:
                    break
                else:
                    self.process(self.last_msg)
        except Exception as e:
            raise e
        self.shutdown()

    def shutdown(self):
        self.sock.close()
