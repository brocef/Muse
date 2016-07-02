from __future__ import unicode_literals
import MuseWorker
import youtube_dl

class MuseCaravan(MuseWorker.MuseWorker):
    def process(self, yt_result, prog_cb):
        self.prog_cb = prog_cb
        ydl_opts = {
            'logger': self,
            'progress_hooks': [self.youtube_dl_progress],
            #'playliststart': 1,
            #'playlistend': 5,
            #'match_filter': match_fitness,
            'verbose': False,
            'quiet': True,
            'ignorecopyright': True,
            'ignoreerrors': True,
            'outtmpl': u'_v%(id)s.mp4'
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download(['https://youtube.com%s' % yt_result['candidate']['link']])
            yt_result['mp4_name'] = '_v%s.mp4' % yt_result['candidate']['id']
            yt_result['mp3_name'] = '_v%s.mp3' % yt_result['candidate']['id']
            return [yt_result]
        print 'Youtube_dl failed on '+str(yt_result)
        return None

    def youtube_dl_progress(self, status):
        if status['status'] == 'downloading':
            self.prog_cb('Downloading', cur_pct=status['downloaded_bytes']/status['total_bytes'])
        elif status['status'] == 'error':
            pass
        elif status['status'] == 'finished':
            self.prog_cb('Finished downloading', cur_pct=1.0)
        else:
            raise Exception('Invalid progress hook '+str(status))

    def debug(self, msg):
        #print 'DEBUG: %s' % (msg)
        pass

    def warning(self, msg):
        #print 'WARNING: %s' % (msg)
        pass

    def error(self, msg):
        print 'ERROR: %s' % (msg)

'''
status_ticker = 0
current_vid = 0
video_count = len(approved)
def my_hook(d):
    global status_ticker
    global current_vid
    global video_count
    status_ticker += 1
    riprint.pr_okblue(('Video file [%d/%d] download complete' % (current_vid, video_count)) + ('.' * (status_ticker % 4) + (' ' * (3 -status_ticker % 4))), True)
    if d['status'] == 'finished':
        current_vid += 1

def match_fitness(info):
    likes = info['like_count']
    dislikes = info['dislike_count']
    total_votes = likes + dislikes
    if likes is 0:
        return 'Skipping %s because it has no likes' % (info['title'])
    like_dislike_ratio = float(likes)/float(dislikes) if dislikes > 0 else float('inf')
    like_total_ratio = float(likes)/float(total_votes)

    if like_total_ratio < 0.90:
        return 'Skipping %s because it has too low a like/total ratio (%f)' % (info['title'], like_total_ratio)

    return None

'''
