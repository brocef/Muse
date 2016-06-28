import Queue

class TBTYBuffer:
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
                return None
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

