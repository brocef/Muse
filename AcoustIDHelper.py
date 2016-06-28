from __future__ import print_function
import acoustid
import sys
import pprint
import re
from math import log

SCORE_BASE = 1.1
STRICT = True
STRICT_THRESHOLD = 2

def nilog(x):
    return -1.0 * log(1.0-x, SCORE_BASE)

reload(sys)
sys.setdefaultencoding('utf8')

API_KEY = 'cSpUJKpD'

def IdentifySoundFile(filename, link_map, min_score=0.5):
    try:
        result_gen = acoustid.match(API_KEY, filename)
    except acoustid.NoBackendError:
        print("chromaprint library/tool not found", file=sys.stderr)
        sys.exit(1)
    except acoustid.FingerprintGenerationError:
        print("fingerprint could not be calculated", file=sys.stderr)
        sys.exit(1)
    except acoustid.WebServiceError as exc:
        print("web service request failed:", exc.message, file=sys.stderr)
        sys.exit(1)

    results = []

    for r in result_gen:
        (score, rid, title, artist) = r
        if title is None or artist is None:
            continue
        results.append(r)
    
    try:
        results = map(lambda r:(nilog(r[0]), r[1], r[2].encode('utf8'), r[3].encode('utf8')), results)
        results = filter(lambda x: x[0]>=nilog(min_score), results)
        return sorted(results, key=lambda k:k[0], reverse=True)
    except AttributeError as e:
        print(results)
        print(e)

def compare_scores(x, y, link_map):
    if x[1] == y[1]: #Scores are equivalent, now adjust based on query params
        (x_track, x_artist, fn) = x[0]
        (y_track, y_artist, y_fn) = y[0]
        assert(fn == y_fn)
        (q, q_param, num) = link_map[fn[:-4]]
        if q_param == 'Artist':
            if q in x_artist and q not in y_artist:
                return 1
            elif q not in x_artist and q in y_artist:
                return -1
            elif q not in x_artist and q not in y_artist:
                pass
        elif q_param == 'Track':
            if q in x_track and q not in y_track:
                return 1
            elif q not in x_track and q in y_track:
                return -1
            elif q not in x_track and q not in y_track:
                pass
    else:
        return cmp(x[1],y[1])
    return 0

def FindMostLikelyTrackArtistPair(results, filename, link_map):
        ta_pairs = dict()
        total = len(results)
        for candidate in results:
            (score, rid, track, artist) = candidate
            if (track, artist, filename) not in ta_pairs:
                ta_pairs[(track, artist, filename)] = []
            ta_pairs[(track, artist, filename)].append(score)

        if STRICT and total > 0 and total < STRICT_THRESHOLD:
            (q, q_param, num) = link_map[filename[:-4]]
            key, score = ta_pairs.popitem()
            (track, artist, filename) = key
            if (q_param == 'Artist' and q not in artist) or (q_param == 'Track' and q not in track):
                print('%s only had one result and strict mode was on, so skipping' % filename)
                return None

        ta_avg_scores = []
        for (key, scores) in ta_pairs.iteritems():
            (track, artist, filename) = key
            intc = len(scores)
            ta_avg_scores.append((key, float(intc) * reduce(lambda acc,x: acc+float(x), scores, 0.0) / float(total)))

        ta_avg_scores = sorted(ta_avg_scores, cmp=lambda x,y: compare_scores(x, y, link_map), reverse=True)
        if len(ta_avg_scores) > 0:
            return ta_avg_scores[0][0]
        else:
            return None
        

