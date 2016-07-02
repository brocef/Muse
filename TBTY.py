import argparse
import os
import threading
from math import log
from difflib import SequenceMatcher
import re
from Queue import Queue, Empty
import random
import time
import riprint
import datetime

from TBTYWorker import TBTYWorker, WORKER_TYPES, WORKER_TYPE_MAP
from TBTYQuery import QUERY_TYPES, TBTYQuery
from TBTYScout import TBTYScout
from TBTYDoctor import TBTYDoctor
from TBTYAgent import TBTYAgent
from TBTYCaravan import TBTYCaravan
from TBTYFriend import TBTYFriend
from TBTYBuffer import TBTYBuffer

SCORE_BASE = 1.1

def nilog(x):
    return -1.0 * log(1.0-x, SCORE_BASE)

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

STAGES = ('search', 'video', 'extract', 'identify', 'import')
W_TYPE_STG_MAP = dict(zip(WORKER_TYPES, STAGES))
STAGE_CONSTRS = (
            lambda config, w_id, in_q, out_q, prog_cb: TBTYScout(config, w_id, in_q, out_q, prog_cb),
            lambda config, w_id, in_q, out_q, prog_cb: TBTYCaravan(config, w_id, in_q, out_q, prog_cb),
            lambda config, w_id, in_q, out_q, prog_cb: TBTYDoctor(config, w_id, in_q, out_q, prog_cb),
            lambda config, w_id, in_q, out_q, prog_cb: TBTYAgent(config, w_id, in_q, out_q, prog_cb),
            lambda config, w_id, in_q, out_q, prog_cb: TBTYFriend(config, w_id, in_q, out_q, prog_cb)
        )
STAGE_INDEX_MAP = {stage:index for (index, stage) in list(enumerate(STAGES))}

DEFAULT_HOME_DIR = '%s/TBTY' % os.getcwd()

def CheckSession(session):
    prog = re.compile(r't_.*_.*_\d+\.tbty')
    return session == None or prog.match(session)

def ParseQuery(query):
    if len(query) == 0:
        err = 'The query cannot be an empty string!'
        raise argparse.ArgumentTypeError(err)
    
    
    spl_query = query.split(':')
    if len(spl_query) != 3:
        err = 'The query must be of the correct form Q:T:N'
        raise argparse.ArgumentTypeError(err)

    if spl_query[1] not in QUERY_TYPES:
        err = 'The query type must be one of the following: %s' % str(QUERY_TYPES)
        raise argparse.ArgumentTypeError(err)

    try:
        spl_query[2] = int(spl_query[2])
    except ValueError:
        err = 'The query count must be a natural number'
        raise argparse.ArgumentTypeError(err)

    # TODO: Figure out if the query comes in already encoded/decoded and then spawn an appropriately
    #   encoded alternative since the search query url needs a utf-8 urllib quote_plus() encoding
    return TBTYQuery(spl_query)
    
def SafeParseQuery(query):
    try:
        return ParseQuery(query) != None
    except Exception:
        return False

def ParseArgs():
    parser = argparse.ArgumentParser(prog='TBTY')
    parser.add_argument('-S --start-stage', dest='initial_stage', choices=STAGES, default=STAGES[0],
            help='The stage %(prog)s should start with (default %(default)r)')
    parser.add_argument('-F --final-stage', dest='terminal_stage', choices=STAGES, default=STAGES[len(STAGES)-1],
            help='The stage %(prog)s should finish with (default %(default)s)')
    parser.add_argument('-D --home-dir', dest='home_dir', metavar='HOME_DIR_PATH', default=DEFAULT_HOME_DIR,
            help='The directory in which TBTY stage folders are created (default %(default)s)')
    parser.add_argument('queries', nargs='+', metavar='Q:Type:N|SESSION NAME',
            help='Search queries to use when scraping YouTube or the name of a previous session. You can also improve accuracy of the scraper by taggint your query type in the following form: Q:{Artist,Track,Album,*}:N. For example, RZA:Artist:10 would start a search for a maximum of 10 candidate tracks of the Artist, RZA. Big Boi:*:10 for any video from the query Big Boi.')
    parser.add_argument('-R --resume', dest='resume', action='store_const', const=True, default=False,
            help='Resume a past session instead of starting a new one with a new query.')
    args = parser.parse_args()
    if not args.resume:
        if not reduce(lambda acc, x: acc and SafeParseQuery(x), args.queries, True):
            parser.print_help()
            raise argparse.ArgumentTypeError('A query was malformed. Were you intending to resume a session instead?')

    if STAGE_INDEX_MAP[args.initial_stage] > STAGE_INDEX_MAP[args.terminal_stage]:
        raise argparse.ArgumentTypeError('The final stage cannot happen before the start stage!')
    return args

class TBTYConfig(object):
    def __init__(self, parsed_args):
        self.resume = parsed_args.resume
        self.initial_stage = STAGE_INDEX_MAP[parsed_args.initial_stage]
        self.terminal_stage = STAGE_INDEX_MAP[parsed_args.terminal_stage]
        self.home_dir = parsed_args.home_dir
        self.queries = parsed_args.queries if self.resume else map(ParseQuery, parsed_args.queries)
        self._createSystemResources()
        if self.resume == None:
            self.resume = False
            self._loadConfig(self.resume)
        self._DELIMITER = '.'
        self.stage_count = self.terminal_stage - self.initial_stage + 1

    def _loadConfig(self):
        pass

    def _createSystemResources(self):
        if os.path.exists(self.home_dir):
            if not os.path.isdir(self.home_dir):
                raise IOError('Provided home directory already exists, but not as a directory')
        else:
            # TODO: create a better file system for this, maybe:
            # TBTY/Sessions/SESSIONX/SCOUT
            os.mkdir(self.home_dir)
#t_.*_.*_\d+\
        self.timestamp = datetime.datetime.now().strftime('%H%M%S')
        self.session_name = 't_%s.tbty' % (self.timestamp)
        self.query_folder_names = map(lambda q: 't_%s_%s_%s' % (q.getQueryTerm(), q.getQueryType(), self.timestamp), self.queries)
        self.query_folder_map = map(zip(self.query_folder_names, self.queries))
        for f in self.query_folder_names:
            os.mkdir(f)

    def doesSessionExist(self, session):
        return os.path.exists(os.path.join(os.home_dir, session))

    # THESE ARE THE NUMERIC INDEX OF THE STAGE IN STAGE_INDEX_MAP
    def getInitialStage(self):
        return self.initial_stage
    
    def getTerminalStage(self):
        return self.terminal_stage

    def getStages(self):
        return range(self.getInitialStage(), self.getTerminalStage()+1)

    def getStageCount(self):
        return self.stage_count

    def getQueries(self):
        return list(self.queries)

    def getHomeDirectoryPath(self):
        return self.home_dir

    def stringify(self):
        return '[%s, %s]=>%s\n%s' % (STAGES[self.initial_stage], STAGES[self.terminal_stage], self.home_dir, str(map(lambda x: x.stringify(), self.queries)))

class TBTY(object):
    def __init__(self, config):
        self.config = config
        self.progress_lock = threading.Lock()
        self.cur_pct = 0.0
        self.status_str = 'Initializing...'
        self.all_stages = self.config.getStages()
        self.cur_stage = self.all_stages[0]-1
        self.authors = ['NIT'] + list(WORKER_TYPES)

    def progress_hook(self, status_str, cur_pct=None):
        self.progress_lock.acquire()
        if cur_pct != None:
            self.cur_pct = cur_pct
        self.status_str = status_str
        self.report_progress()
        self.progress_lock.release()

    def report_progress(self):
        vis_stages = ''
        for s in self.config.getStages():
            vis_stages += '[%s]' % ('x' if self.cur_stage >= s else ' ')
        riprint.pr_okblue('% -60s % +15s' % ('%s %s (%.2f%s)' % (self.authors[self.cur_stage+1], self.status_str, 100.0*float(self.cur_pct), '% done'), vis_stages), True)

    def run(self):
        stage_qs = list()
        workers = list()
        self.report_progress()

        stage_qs.append(Queue())
        for i in self.config.getStages():
            stage_qs.append(Queue())
            w_id = '%s%02d' % (WORKER_TYPES[i], i)
            workers.append(STAGE_CONSTRS[i](self.config, w_id, stage_qs[i], stage_qs[i+1], self.progress_hook))

        for stage in self.config.getStages():
            if stage == 0: # Special case, not from an old stage output, but the user
                for q in self.config.getQueries():
                    stage_qs[0].put(q)
                stage_qs[0].put(None)

        map(lambda t: t.start(), workers)

        #print 'Joining on stage threads'
        for t in workers:
            self.progress_hook('Task completed', cur_pct=1.0)
            print('')
            self.cur_stage = self.all_stages.pop(0)
            t.join()
            #print '%s has completed its tasks!' % t.getID()
        self.report_progress()
        print ''
        # Shutoff
        #print 'Shutting down...'

if __name__ == '__main__':
    config = TBTYConfig(ParseArgs())
    tbty = TBTY(config)
    tbty.run()
