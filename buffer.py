import random
import Queue

BUF_SIZE = 8
_COUNT = 0
_BUFFER = ''

def genRandInput():
    global _BUFFER
    le_str = ''
    for i in xrange(0, random.randint(1,10)):
        le_str += genInput(random.randint(2, 8))
    _BUFFER += le_str
    end_index = min(len(_BUFFER), BUF_SIZE)
    first_chunk = _BUFFER[:end_index]
    _BUFFER = _BUFFER[end_index:]
    return first_chunk

def genInput(data_len):
    global _COUNT, _BUFFER
    s = ''
    for i in xrange(0, data_len):
        s += chr(ord('a') + _COUNT % 26)
        _COUNT  += 1
    return s + '!'

class StreamBuffer:
    def __init__(self, input_src, delimiter):
        self._data = ''
        self._ptr = 0
        self.queue = Queue.Queue()
        self.input_src = input_src
        self.delimiter = delimiter

    def get_msg(self):
        if not self.queue.empty():
            return self.queue.get()

        while 1:
            newdata = self.input_src()
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

        return self.queue.get()

def genPredInput():
    return 'abcdefg!hijklmnopqr!stuvwx!y!z!'

checksum = 0
buf = StreamBuffer(genRandInput, '!')
for i in xrange(0, 5000):
    m = buf.get_msg()
    assert(len(m) <= BUF_SIZE)
    for j in xrange(0, len(m)):
        assert(ord(m[j])-ord('a') == checksum)
        checksum = (checksum + 1) % 26
    print i, m
