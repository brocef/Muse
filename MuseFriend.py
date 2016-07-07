import MuseWorker
import os

class MuseFriend(MuseWorker.MuseWorker):
    def process(self, yt_result, prog_cb):
        if yt_result['identity']:
            better_name = os.path.join(self.config.cur_session_dir, '%(artist)s - %(track)s.mp3' % yt_result['identity'])
            os.rename(yt_result['mp3_name'], better_name)
            yt_result['mp3_name'] = better_name
        return [yt_result]
