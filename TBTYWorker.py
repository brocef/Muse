import threading
import socket
import re
import Queue
from abc import ABCMeta, abstractmethod
from TBTYBuffer import TBTYBuffer

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
        self.tbuf = None

    @staticmethod
    def parse_msg(message):
        m = re.match(r'^<([A-Z]+)>(.+)$', message)
        return m.groups() if m is not None else (None, None)

    def send_msg(self, message):
        self.sock.sendall('<%s>%s\n' % (self.w_type, message))

    def recv_msg(self):
        msg = self.tbuf.get_msg()

        if not msg:
            return False

        self.last_msg = msg
        return True
        
    
    @abstractmethod
    def process(self, data):
        raise Exception('Cannot process data')

    def init(self, worker_type):
        self.w_type = worker_type
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.config.getServerAddress())
        self.recv_sock = lambda: self.sock.recv(self.BUF_SIZE)
        self.tbuf = TBTYBuffer(self.recv_sock, '\n')
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
