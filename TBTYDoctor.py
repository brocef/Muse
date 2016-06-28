import TBTYWorker

class TBTYDoctor(TBTYWorker.TBTYWorker):
    def run(self):
        self.init(self.TYPES[2])

    def process(self, data):
        self.send_msg(data)
