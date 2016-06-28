import TBTYWorker

class TBTYCaravan(TBTYWorker.TBTYWorker):
    def run(self):
        self.init(self.TYPES[1])

    def process(self, data):
        self.send_msg(data)
