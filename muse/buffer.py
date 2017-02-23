import Queue

class MuseBuffer:
    def __init__(self, input_src, delimiter):
        self._data = ''
        self._ptr = 0
        self.queue = Queue.Queue()
        self.input_src = input_src
        self.delimiter = delimiter

    def get_q_size(self):
        return self.queue.qsize()

    def get_msg(self):
        if not self.queue.empty():
            return self.queue.get(False)

        delimFound = False
        failsafe = 0
        while not delimFound and failsafe < 3:
            newdata = self.input_src()
            failsafe += 1
            if not newdata or len(newdata) == 0:
                #raise Exception('Failed to buffer new data')
                return None
            self._data += newdata
            print 'current data %s' % self._data
            while self._ptr < len(self._data):
                if self._data[self._ptr] == self.delimiter:
                    ex_msg = self._data[:self._ptr]
                    self.queue.put(ex_msg)
                    self._data = self._data[self._ptr+1:]
                    self._ptr = 0
                    delimFound = True
                else:
                    self._ptr += 1

        return self.queue.get(False)

