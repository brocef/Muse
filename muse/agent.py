from . import worker
import sys
import acoustid
from math import log

SCORE_BASE = 1.1
STRICT = False
STRICT_THRESHOLD = 2

def nilog(x):
    return -1.0 * log(1.0-x, SCORE_BASE)

reload(sys)
sys.setdefaultencoding('utf8')

API_KEY = 'cSpUJKpD'

def compare_scores(x, y, query):
    net_score = 0
    if x[1] == y[1]: #Scores are equivalent, now adjust based on query params
        (x_track, x_artist, rid) = x[0]
        (y_track, y_artist, y_rid) = y[0]
        (q, q_terms) = query
        for (q_term, term_type) in q_terms:
            if term_type == 'Artist':
                if q_term in x_artist:
                    net_score += 1
                if q_term in y_artist:
                    net_score += -1
            elif term_type == 'Track':
                if q_term in x_track:
                    net_score += 1
                if q_term in y_track:
                    net_score += -1
    else:
        return cmp(x[1],y[1])
    return net_score

class Agent(worker.Worker):
    def process(self, yt_result, prog_cb):
        try:
            if yt_result['CVN'] == 'download_success':
                prog_cb('Attempting to Identify Track')
                aid = self.IdentifySoundFile(yt_result)
                likely = self.FindMostLikelyTrackArtistPair(aid, yt_result)
                if likely:
                    best_tuple, best_score = likely
                    (track, artist, rid) = best_tuple
                    best = {
                        'artist': artist,
                        'track': track,
                        'rid': rid,
                        'score': best_score
                    }
                    yt_result['identity'] = best
                else:
                    try:
                        del yt_result['identity']
                    except KeyError:
                        pass
        except acoustid.NoBackendError:
            self.eprint("chromaprint library/tool not found")
            sys.exit(1)
            #return None
        except acoustid.FingerprintGenerationError:
            self.eprint("fingerprint could not be calculated")
            sys.exit(1)
            #return None
        except acoustid.WebServiceError as exc:
            self.eprint("web service request failed:", exc.message)
            sys.exit(1)
            #return None

        yield yt_result

    def IdentifySoundFile(self, yt_result, min_score=0.5):
        result_gen = acoustid.match(API_KEY, yt_result['mp3_path'])

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
            self.eprint(results)
            self.eprint(e)


    def FindMostLikelyTrackArtistPair(self, acoustid_results, yt_result):
            ta_pairs = dict()
            total = len(acoustid_results)
            for candidate in acoustid_results:
                (score, rid, track, artist) = candidate
                if (track, artist, rid) not in ta_pairs:
                    ta_pairs[(track, artist, rid)] = []
                ta_pairs[(track, artist, rid)].append(score)

            q = yt_result['query']
            q_terms = yt_result['query_terms']
            num = yt_result['query_num_pages']

            '''
            if STRICT and total > 0 and total < STRICT_THRESHOLD:
                key, score = ta_pairs.popitem()
                (track, artist, rid) = key
                if (q_param == 'Artist' and q not in artist) or (q_param == 'Track' and q not in track):
                    #self.eprint('%s only had one result and strict mode was on, so skipping' % yt_result['mp3_name'])
                    return None
            '''

            ta_avg_scores = []
            for (key, scores) in ta_pairs.iteritems():
                (track, artist, rid) = key
                intc = len(scores)
                ta_avg_scores.append((key, float(intc) * reduce(lambda acc,x: acc+float(x), scores, 0.0) / float(total)))

            ta_avg_scores = sorted(ta_avg_scores, cmp=lambda x,y: compare_scores(x, y, (q, q_terms)), reverse=True)
            if len(ta_avg_scores) > 0:
                return ta_avg_scores[0]
            else:
                return None

