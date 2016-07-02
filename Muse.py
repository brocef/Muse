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
import pickle

from MuseWorker import MuseWorker, WORKER_TYPES, WORKER_TYPE_MAP
from MuseQuery import QUERY_TYPES, MuseQuery
from MuseScout import MuseScout
from MuseDoctor import MuseDoctor
from MuseAgent import MuseAgent
from MuseCaravan import MuseCaravan
from MuseFriend import MuseFriend
from MuseBuffer import MuseBuffer

SCORE_BASE = 1.1

def nilog(x):
    return -1.0 * log(1.0-x, SCORE_BASE)

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

STAGES = ('search', 'video', 'extract', 'identify', 'import')
W_TYPE_STG_MAP = dict(zip(WORKER_TYPES, STAGES))
STAGE_CONSTRS = (
            lambda config, w_id, in_q, out_q, prog_cb: MuseScout(config, w_id, in_q, out_q, prog_cb),
            lambda config, w_id, in_q, out_q, prog_cb: MuseCaravan(config, w_id, in_q, out_q, prog_cb),
            lambda config, w_id, in_q, out_q, prog_cb: MuseDoctor(config, w_id, in_q, out_q, prog_cb),
            lambda config, w_id, in_q, out_q, prog_cb: MuseAgent(config, w_id, in_q, out_q, prog_cb),
            lambda config, w_id, in_q, out_q, prog_cb: MuseFriend(config, w_id, in_q, out_q, prog_cb)
        )
STAGE_INDEX_MAP = {stage:index for (index, stage) in list(enumerate(STAGES))}

DEFAULT_HOME_DIR = os.path.join(os.getcwd(), 'Muse')
DEFAULT_SESSIONS_DIR = os.path.join(DEFAULT_HOME_DIR, 'Sessions')

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
    return MuseQuery(spl_query)
    
def SafeParseQuery(query):
    try:
        return ParseQuery(query) != None
    except Exception:
        return False

def ParseArgs():
    parser = argparse.ArgumentParser(prog='Muse')
    parser.add_argument('-D --home-dir', dest='home_dir', metavar='HOME_DIR_PATH', default=DEFAULT_HOME_DIR, help='The directory in which Muse stage folders are created (default %(default)s)')

    subparsers = parser.add_subparsers(dest='mode', help='Subparser help')
    discover_parser = subparsers.add_parser('discover', help='discover help')
    #discover_parser.add_argument('-S --start-stage', dest='initial_stage', choices=STAGES, default=STAGES[0], help='The stage %(prog)s should start with (default %(default)r)')
    discover_parser.add_argument('-F --final-stage', dest='terminal_stage_name', choices=STAGES, default=STAGES[len(STAGES)-1], help='The stage %(prog)s should finish with (default %(default)s)')
    discover_parser.add_argument('queries', nargs='+', type=ParseQuery, metavar='Query:QUERY TYPE:Approx Result Count', help='Search queries to use when scraping YouTube. You can also improve accuracy of the scraper by tagging your query type in the following form: Q:{Artist,Track,Album,*}:N. For example, RZA:Artist:10 would start a search for a maximum of 10 candidate tracks of the Artist, RZA. Big Boi:*:10 for any video from the query Big Boi.')

    resume_parser = subparsers.add_parser('resume', help='resume help')
    resume_parser.add_argument('session', metavar='SESSION_NAME', type=str, help='Session name help')
    #parser.add_argument('queries', nargs='+', metavar='Q:Type:N|SESSION NAME',
    #        help='Search queries to use when scraping YouTube or the name of a previous session. You can also improve accuracy of the scraper by tagging your query type in the following form: Q:{Artist,Track,Album,*}:N. For example, RZA:Artist:10 would start a search for a maximum of 10 candidate tracks of the Artist, RZA. Big Boi:*:10 for any video from the query Big Boi.')
    #parser.add_argument('-R --resume', dest='resume', action='store_const', const=True, default=False,
    #        help='Resume a past session instead of starting a new one with a new query.')
    
    args = parser.parse_args()
    if args.mode == 'discover':
        args.terminal_stage = STAGE_INDEX_MAP[args.terminal_stage_name]
    #if not args.resume:
    #    if not reduce(lambda acc, x: acc and SafeParseQuery(x), args.queries, True):
    #        parser.print_help()
    #        raise argparse.ArgumentTypeError('A query was malformed. Were you intending to resume a session instead?')

    #if STAGE_INDEX_MAP[args.initial_stage] > STAGE_INDEX_MAP[args.terminal_stage]:
    #    raise argparse.ArgumentTypeError('The final stage cannot happen before the start stage!')
    return vars(args)

DEFAULT_CONFIG = {
    'home_dir': DEFAULT_HOME_DIR,
    'sessions_dir': DEFAULT_SESSIONS_DIR,
    'terminal_stage': STAGES[len(STAGES)-1]
}
class MuseConfig(object):
    def __init__(self, parsed_args):
        self.cfg = parsed_args
        self.config_path = os.path.join(self.cfg['home_dir'], 'config.txt')
        from_cfg = self._loadConfig(self.config_path)
        for key,val in from_cfg.iteritems():
            if key not in self.cfg:
                # Overwrite value in cfg
                self.cfg[key] = val

        for key,val in self.cfg.iteritems():
            setattr(self, key, val)


        if self.mode == 'discover':
            self.session = datetime.datetime.now().strftime('%a%j_%H%M%S').upper()
            self.cur_session_dir = os.path.join(self.sessions_dir, self.session)
            self.terminal_stage = STAGE_INDEX_MAP[self.terminal_stage_name]
        elif self.mode == 'resume':
            self.cur_session_dir = os.path.join(self.sessions_dir, self.session)

        self.manifest_path = os.path.join(self.cur_session_dir, 'manifest.txt')
        self._ensureSystemResources()
        '''
        self.resume = parsed_args.resume
        #self.initial_stage = STAGE_INDEX_MAP[parsed_args.initial_stage]
        self.initial_stage = 0
        self.terminal_stage = STAGE_INDEX_MAP[parsed_args.terminal_stage]
        self.queries = parsed_args.queries if self.resume else map(ParseQuery, parsed_args.queries)
        self._createSystemResources()
        if self.resume == None:
            self.resume = False
            self._loadConfig(self.resume)
        self._DELIMITER = '.'
        self.stage_count = self.terminal_stage - self.initial_stage + 1
        self.sessions_dir = os.path.join(self.home_dir, 'sessions')
        if self.resume:
            self.cur_session_dir = self.queries
            pass
        else:
            self.timestamp = datetime.datetime.now().strftime('%a_%H%M%S').upper()
            self.cur_session_dir = os.path.join(self.sessions_path, self.timestamp)
            self.cur_session_path = os.path.join(self.cur_session_dir, 'manifest.txt')
        '''
    @staticmethod
    def _loadConfig(configPath):
        configData = None
        if os.path.exists(configPath) and os.path.isfile(configPath):
            with open(configPath, 'r') as config:
                try:
                    configData = pickle.load(config)
                except EOFError:
                    configData = DEFAULT_CONFIG
        else:
            configData = DEFAULT_CONFIG
        return configData

    def saveConfig(self):
        with open(self.config_path, 'w') as config:
            pickle.dump(self.cfg, config)


    def _ensureSystemResources(self):
        MuseConfig._ensureDirCreation(self.home_dir)
        MuseConfig._ensureDirCreation(self.sessions_dir)
        MuseConfig._ensureDirCreation(self.cur_session_dir)
        if self.mode == 'resume':
            MuseConfig._ensureFileExists(self.manifest_path)
        elif self.mode == 'discover':
            pass
        
    @staticmethod
    def _ensureFileExists(path):
        assert(os.path.exists(path) and os.path.isfile(path))

    @staticmethod
    def _ensureDirCreation(path):
        if os.path.exists(path):
            if not os.path.isdir(path):
                raise IOError('Specified directory ('+path+') already exists, but not as a directory')
        else:
            os.mkdir(path)

    def doesSessionExist(self, session):
        return os.path.exists(os.path.join(os.home_dir, session))

    # THESE ARE THE NUMERIC INDEX OF THE STAGE IN STAGE_INDEX_MAP
    #def getInitialStage(self):
    #    return self.initial_stage
    
    def discover(self):
        return self.mode == 'discover'

    def resume(self):
        return self.mode == 'resume'

    def getTerminalStage(self):
        return self.terminal_stage

    def getStages(self):
        return range(0, self.getTerminalStage()+1)

    def getStageCount(self):
        return self.stage_count

    def getQueries(self):
        return list(self.queries)

    def getHomeDirectoryPath(self):
        return self.home_dir

    def stringify(self):
        return '[%s, %s]=>%s\n%s' % (STAGES[0], STAGES[self.terminal_stage], self.home_dir, str(map(lambda x: x.stringify(), self.queries)))

class Muse(object):
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

        if self.config.discover():
            for stage in self.config.getStages():
                if stage == 0: # Special case, not from an old stage output, but the user
                    for q in self.config.getQueries():
                        stage_qs[0].put(q)
                    stage_qs[0].put(None)
        elif self.config.resume():
            with open(self.config.manifest_path, 'r') as manifest:
                stage_imports = pickle.load(manifest)
                for q_index,data in stage_imports.iteritems():
                    for e in data:
                        stage_qs[q_index].put(e)

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

        # Save output to appropriately and make the manifest
        stage_results = []
        for q in stage_qs:
            stage_results.insert(0, [])
            while not q.empty():
                stage_results[0].append(q.get())
        stage_results.reverse()
        with open(self.config.manifest_path, "w") as manifest: 
            pickle.dump(dict(enumerate(stage_results)), manifest)

        self.config.saveConfig()

if __name__ == '__main__':
    config = MuseConfig(ParseArgs())
    muse = Muse(config)
    muse.run()
