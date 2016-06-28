import TBTYWorker

class TBTYAgent(TBTYWorker.TBTYWorker):
    def run(self):
        self.init(self.TYPES[3])

    def process(self, data):
        self.send_msg(data)
