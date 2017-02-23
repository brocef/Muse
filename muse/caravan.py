from __future__ import unicode_literals
import worker
import youtube_dl
import os
import sys

class MuseCaravan(worker.worker):
    def __init__(self, *args):
        super(MuseCaravan, self).__init__(*args)
        self.video_count = 0
        self.name_format = '_v%s_%s_%s' % ('%s', self.w_id, '%04d.%s')
    
    def process(self, yt_result, prog_cb):
        self.prog_cb = prog_cb
        mp4n = self.name_format % (yt_result['candidate']['id'], self.video_count, 'mp4')
        mp3n = self.name_format % (yt_result['candidate']['id'], self.video_count, 'mp3')
        yt_result['mp4_name'] = mp4n
        yt_result['mp3_name'] = mp3n

        ydl_opts = {
            'logger': self,
            'progress_hooks': [self.youtube_dl_progress],
            'verbose': False,
            'quiet': True,
            'ignorecopyright': True,
            'ignoreerrors': True,
            'merge_output_format': 'mp4',
            'format': 'mp4',
            'outtmpl': unicode(os.path.join(self.config.cur_session_dir, yt_result['mp4_name']))
        }
        yt_result['CVN'] = 'download_failure'
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            #mp4n = '_v%s.mp4' % yt_result['candidate']['id']
            #mp3n = '_v%s.mp3' % yt_result['candidate']['id']
            mp4path = unicode(os.path.join(self.config.cur_session_dir, mp4n))
            mp3path = unicode(os.path.join(self.config.cur_session_dir, mp3n))
            if os.path.isfile(mp4path):
                # File already exists... how?
                # TODO: track this down
                yt_result['CVN'] = 'download_duplicate_failure'
            elif ydl.download(['https://youtube.com%s' % yt_result['candidate']['link']]) == 0:
                yt_result['mp3_path'] = mp3path
                yt_result['mp4_path'] = mp4path
                if os.path.isfile(yt_result['mp4_path']):
                    yt_result['CVN'] = 'download_success'
                else:
                    del yt_result['mp4_name']
                    del yt_result['mp3_name']
                    del yt_result['mp3_path']
                    del yt_result['mp4_path']
                    yt_result['CVN'] = 'download_failure'

        self.video_count += 1
        yield yt_result
        #print 'Youtube_dl failed on '+str(yt_result)
        #yield None

    def estimateProb(self):
        return super(MuseCaravan, self).estimateProb()

    def youtube_dl_progress(self, status):
        if status['status'] == 'downloading':
            #pct = float(status['_percent_str'][:-1])/100.0
            self.prog_cb('Downloading (%s)' % status['_percent_str'])
        elif status['status'] == 'error':
            self.err_cb('Error while downloading!', error=-1.0)
        elif status['status'] == 'finished':
            self.prog_cb('Finished downloading')
        else:
            raise Exception('Invalid progress hook '+str(status))

    def debug(self, msg):
        #print 'DEBUG: %s' % (msg)
        pass

    def warning(self, msg):
        #print 'WARNING: %s' % (msg)
        self.eprint(msg)

    def error(self, msg):
        # print 'ERROR: %s' % (msg)
        # sys.exit(1)
        self.eprint(msg)
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
