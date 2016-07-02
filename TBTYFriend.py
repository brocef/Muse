import TBTYWorker
import os

class TBTYFriend(TBTYWorker.TBTYWorker):
    def process(self, yt_result, prog_cb):
        if yt_result['identity']:
            os.rename(yt_result['mp3_name'], '%(artist)s - %(track)s.mp3' % yt_result['identity'])
        return [yt_result]
