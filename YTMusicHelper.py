# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from pprint import pprint
import urllib
from YTScraper import ScrapeYT
from YTSearchFilter import FilterResults
from AcoustIDHelper import IdentifySoundFile, FindMostLikelyTrackArtistPair
import youtube_dl
import subprocess
import os
import riprint

'''
    Search queries are of the following form
        (Search Term, {Artist,Track,Album,*}, Page Scrape Amount)
       **ONLY Artist AND Track ARE SUPPORTED CURRENTLY**

    ex. ('Jay-Z', 'Artist', 2) will scrape 2 pages of YT search results, a total of 40 videos,
                                from YT's search feature given the term 'Jay-Z'. This program will
                                also use the query type (the second argument) to make a more accurate
                                baseline analysis by weighing the AcoustID results accordingly.

    Note: Each page contains a maximum of 20 video results, so the last argument should be a
            small number, likely under 10, as the decreased quality and relevance of the latter
            results yields a poorer performance, not to mention the many duplicates that inevitably
            crop up.
'''
_search_queries = [
        (u'Brittney Spears', 'Artist', 2)
        ]

search_queries = map(lambda x: (urllib.quote_plus(x[0].encode('utf-8')), x[1], x[2]), _search_queries)

results = ScrapeYT(search_queries, _search_queries)

# Create a mapping of the video's url ID to the query used to find the video
# This mapping is necessary to help process AcoustID fingerprint candidates, as the query's similarity
#   to the track name or artist (if Track or Arist was the parameter in the search query tuple)
#   will be accounted for to yield a more likey result
f_link_map = dict()
for r in results:
    link = r['candidate']['link']
    f_link_map['v'+link[link.find('v=')+2:]] = r['decoded_query']

#for key, val in f_link_map.iteritems():
#    print key, reduce(lambda acc, y: '%s %s' % (acc, y), val, '')

(approved, rejected) = FilterResults(results)

class MyLogger(object):
    def debug(self, msg):
        #print 'DEBUG: %s' % (msg)
        pass

    def warning(self, msg):
        #print 'WARNING: %s' % (msg)
        pass

    def error(self, msg):
        print 'ERROR: %s' % (msg)

my_logger = MyLogger()

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

ydl_opts = {
    'logger': my_logger,
    'progress_hooks': [my_hook],
    'playliststart': 1,
    'playlistend': 5,
    'match_filter': match_fitness,
    'ignorecopyright': True,
    'ignoreerrors': True,
    'outtmpl': 'v%(id)s.mp4'
}

with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    ydl.download(map(lambda x : 'https://www.youtube.com%s' % x['candidate']['link'], approved))

successes = []
failures = []
# Now, extract the audio and remove the video
for r in approved:
    fn_mp3 = 'v%s.mp3' % r['candidate']['id']
    fn_mp4 = 'v%s.mp4' % r['candidate']['id']
    if os.path.isfile(fn_mp4):
        successes.append(r)
        subprocess.call(['ffmpeg', '-loglevel', 'panic', '-i', fn_mp4, '-vn', '-sn', '-c:a', 'mp3', '-ab', '192k', fn_mp3])
        os.remove(fn_mp4)
        subprocess.call(['eyeD3', '-l', 'error', '-Q', '--remove-all', fn_mp3])
        
        acoustid = IdentifySoundFile(fn_mp3, f_link_map)
        best = FindMostLikelyTrackArtistPair(acoustid, fn_mp3, f_link_map)
        print fn_mp3, best
        if best is not None:
            successes.append(r)
        else:
            failures.append(r)
    else:
        # This is actually okay, as videos can fail due to errors or removal/deletion from YT
        #raise Exception('The video with id %s failed to download!' % r['candidate']['link'])
        failures.append(r)

# Finally, calculate the baseline accuracy for the approved videos
print('Classification success count: %d' % len(successes))
print('Classification failure count: %d' % len(failures))



'''
print 'Approved:'
pprint(approved)
print ''
print 'Rejected:'
pprint(rejected)
'''

