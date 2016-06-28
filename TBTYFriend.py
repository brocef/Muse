import TBTYWorker

class TBTYFriend(TBTYWorker.TBTYWorker):
    def run(self):
        self.init(self.TYPES[4])

    def process(self, data):
        self.send_msg(data)
