import argparse
import os
import threading
from math import log
from difflib import SequenceMatcher
import re
from Queue import Queue, Empty
import random
import time
import datetime
import pickle
from StringIO import StringIO

from MuseWorker import MuseWorker, WORKER_TYPES, WORKER_TYPE_MAP
from MuseQuery import QUERY_TYPES, MuseQuery
from MuseScout import MuseScout
from MuseDoctor import MuseDoctor
from MuseAgent import MuseAgent
from MuseCaravan import MuseCaravan
from MuseFriend import MuseFriend
from MuseBuffer import MuseBuffer
from MuseUI import MuseUI
from MuseSessionCompiler import MuseSessionCompiler

SCORE_BASE = 1.1

def nilog(x):
    return -1.0 * log(1.0-x, SCORE_BASE)

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

STAGES = ('search', 'video', 'extract', 'identify', 'import')
W_TYPE_STG_MAP = dict(zip(WORKER_TYPES, STAGES))
STAGE_CLASSES = (MuseScout, MuseCaravan, MuseDoctor, MuseAgent, MuseFriend)
STAGE_INDEX_MAP = {stage:index for (index, stage) in list(enumerate(STAGES))}

DEFAULT_HOME_DIR = os.path.join(os.getcwd(), 'Muse')
DEFAULT_SESSIONS_DIR = os.path.join(DEFAULT_HOME_DIR, 'Sessions')

term_re = re.compile(r'([^:]+):(Artist|Track|Album)')
def ParseQueryTerm(term):
    m = term_re.match(term)
    if m:
        return m.groups()
    else:
        return False

query_re = re.compile(r'^(.+:)(\d+)$')
gen_term_re = re.compile(r'(\s?([^{}]+)[\s:])|([{]([^{}]+)[}][\s:])')
def ParseQuery(query):
    if len(query) == 0:
        err = 'The query cannot be an empty string!'
        raise argparse.ArgumentTypeError(err)
    
    m = query_re.match(query)
    if m:
        (query_line, num) = m.groups()
        terms = []
        clean_query = ''
        for match in gen_term_re.finditer(query_line):
            (_, q_raw_term, _, q_term) = match.groups()
            if q_term == None:
                clean_query = '%s %s' % (clean_query, q_raw_term)
            elif q_raw_term == None:
                p_term = ParseQueryTerm(q_term)
                if p_term:
                    terms.append(p_term)
                    clean_query = '%s %s' % (clean_query, p_term[0])
                else:
                    err = 'The query term must be of the correct form {Query:[Artist,Track,Album]}'
                    raise argparse.ArgumentTypeError(err)
        clean_query = clean_query[1:]
        return MuseQuery(clean_query, terms, num)
    else:
        err = 'The query must be similar to the following form: {Queen:Artist} Lyric Videos:5'
        raise argparse.ArgumentTypeError(err)

def SafeParseQuery(query):
    try:
        return ParseQuery(query) != None
    except Exception:
        return False

def ParseArgs():
    parser = argparse.ArgumentParser(prog='Muse')
    parser.add_argument('-D --home-dir', dest='home_dir', metavar='HOME_DIR_PATH', default=DEFAULT_HOME_DIR, help='The directory in which Muse stage folders are created (default %(default)s)')
    parser.add_argument('-F --final-stage', dest='terminal_stage_name', choices=STAGES, default=STAGES[len(STAGES)-1], help='The stage %(prog)s should finish with (default %(default)s)')

    subparsers = parser.add_subparsers(dest='mode', help='Subparser help')
    discover_parser = subparsers.add_parser('discover', help='discover help')
    #discover_parser.add_argument('-S --start-stage', dest='initial_stage', choices=STAGES, default=STAGES[0], help='The stage %(prog)s should start with (default %(default)r)')
    discover_parser.add_argument('queries', nargs='+', type=ParseQuery, metavar='Query:Count', help='Search queries to use when scraping YouTube. You can also improve accuracy of the scraper by tagging your query type in the following form: "Untagged Query Terms {Tagged Query Terms:[Artist,Track,Album]}":N. For example, "{RZA:Artist} Lyric Videos":10 would start a search for a maximum of 10 candidate tracks of the Artist, RZA, with Lyric Videos appended to the query to give better context. Big Boi:10 for any video from the query Big Boi, with no tag heuristics enabled. You may have multiple tagged terms, but they may not be nested.')

    compile_parser = subparsers.add_parser('compile', help='compile help')

    resume_parser = subparsers.add_parser('resume', help='resume help')
    resume_parser.add_argument('session', metavar='SESSION_NAME', type=str, help='Session name help')
    #parser.add_argument('queries', nargs='+', metavar='Q:Type:N|SESSION NAME',
    #        help='Search queries to use when scraping YouTube or the name of a previous session. You can also improve accuracy of the scraper by tagging your query type in the following form: Q:{Artist,Track,Album,*}:N. For example, RZA:Artist:10 would start a search for a maximum of 10 candidate tracks of the Artist, RZA. Big Boi:*:10 for any video from the query Big Boi.')
    #parser.add_argument('-R --resume', dest='resume', action='store_const', const=True, default=False,
    #        help='Resume a past session instead of starting a new one with a new query.')
    
    args = parser.parse_args()
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
        self.config_path = os.path.join(self.cfg['home_dir'], '.config')
        from_cfg = self._loadConfig(self.config_path)
        for key,val in from_cfg.iteritems():
            if key not in self.cfg:
                # Overwrite value in cfg
                self.cfg[key] = val

        for key,val in self.cfg.iteritems():
            setattr(self, key, val)


        self.compile_sessions = False
        if self.mode == 'discover':
            self.session = datetime.datetime.now().strftime('%a%j_%H%M%S').upper()
            self.cur_session_dir = os.path.join(self.sessions_dir, self.session)
            self.terminal_stage = STAGE_INDEX_MAP[self.terminal_stage_name]
        elif self.mode == 'resume':
            self.cur_session_dir = os.path.join(self.sessions_dir, self.session)
        elif self.mode == 'compile':
            self.cur_session_dir = False
            self.compile_sessions = True
            self.stat_hist_path = os.path.join(self.home_dir, '.session_stats')

        if self.cur_session_dir:
            self.manifest_path = os.path.join(self.cur_session_dir, 'manifest')
            self.session_unk_dir = os.path.join(self.cur_session_dir, 'Unknown')
        self._ensureSystemResources()

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
        if self.cur_session_dir:
            MuseConfig._ensureDirCreation(self.cur_session_dir)
            MuseConfig._ensureDirCreation(self.session_unk_dir)
        if self.mode == 'resume':
            MuseConfig._ensureFileExists(self.manifest_path)
        elif self.mode == 'discover':
            pass
        elif self.mode == 'compile':
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
        self.cur_pct = 0.0
        self.all_stages = range(0, config.getTerminalStage()+2)
        self.cur_stage = 0
        self.authors = ['NIT'] + list(WORKER_TYPES)
        self.author_index_map = dict((v, k) for k, v in dict(enumerate(self.authors)).iteritems())
        self.progs = [0 for x in self.authors]
        self.status_strs = ['' for x in self.authors]
        self.ui = MuseUI(self.authors, 10, viewport_width=60, dx=(0, 10), dy=(0, 2))
        self.set_title('Muse')
        self.set_subtitle(' ' + self.config.session)
        for a in xrange(0, len(self.authors)):
            self.report_module_progress(self.status_strs[a], a)
            self.report_module_percent(0.0, a)
        self.set_footer('< :: >         < :: >', 'f_t_f')

    def setProgress(self, line, percent):
        self.ui.setProgress(line, percent)
        self.ui.refresh()

    def setLineText(self, line, text, worker_id=None):
        self.ui.setLineText(line, text, worker_id=worker_id)
        self.ui.refresh()

    def report_module_progress(self, status_str, module_id):
        self.setLineText(module_id + 2, status_str, worker_id=module_id)

    def report_module_percent(self, percent, module_id):
        self.setProgress(module_id + 2, percent)

    def module_callback(self, w_id, status_str, percent):
        w_type = w_id[:3]
        module_id = self.author_index_map[w_type]
        self.report_module_progress(status_str, module_id)
        self.report_module_percent(percent, module_id)

    def set_title(self, title):
        self.ui.setLineTextCustom(0, title, 'center')
        self.ui.refresh()

    def set_subtitle(self, text):
        self.setLineText(1, text)

    def set_footer(self, firstline, secondline):
        self.ui.setLineTextCustom(8, firstline, 'center')
        self.ui.setLineTextCustom(9, secondline, 'center')
        self.ui.refresh()

    def clear_console(self):
        self.ui.clear()
        self.ui.refresh()

    def run(self):
        stage_qs = list()
        workers = list()
        worker_stdout_bufs = list()
        worker_stderr_bufs = list()
        self.cur_stage = self.all_stages.pop(0)
        stage_qs.append(Queue())
        self.report_module_progress('Initializing Muse', 0)
        self.report_module_percent(0.0, 0)
        for i in xrange(0, len(self.config.getStages())):#self.config.getStages():
            #prog_cb = lambda status, cur_pct: self.progress_hook(status, i+1, cur_pct)
            stage_qs.append(Queue())
            #prog_cb('test', 0.5)
            w_id = '%s%02d' % (WORKER_TYPES[i], i)

            out_buf = open(w_id+'.out', 'w')
            err_buf = open(w_id+'.err', 'w')
            #out_buf = StringIO()
            #err_buf = StringIO()
            worker_stdout_bufs.append(out_buf)
            worker_stderr_bufs.append(err_buf)
            workers.append(STAGE_CLASSES[i](self.config, w_id, stage_qs[i], stage_qs[i+1], self.module_callback, out_buf, err_buf))
        
        if self.config.discover():
            for stage in self.config.getStages():
                if stage == 0: # Special case, not from an old stage output, but the user
                    for q in self.config.getQueries():
                        stage_qs[0].put((q, len(self.config.getQueries())))
        elif self.config.resume():
            with open(self.config.manifest_path, 'r') as manifest:
                stage_imports = pickle.load(manifest)
                for q_index,data in stage_imports.iteritems():
                    for e in data:
                        stage_qs[q_index].put(e)
        stage_qs[0].put(None)
        #workers[1].testReport()
        #return
        map(lambda t: t.start(), workers)

        self.report_module_progress('Initialization complete', 0)
        self.report_module_percent(1.0, 0)
        #print 'Joining on stage threads'
        self.report_module_progress('-WORKER SHUTDOWN-', self.cur_stage)
        self.report_module_percent(('---%', '%d item%s' % (0 if not self.config.discover() else len(self.config.getQueries()), 's' if len(self.config.getQueries()) != 1 else '')), self.cur_stage)
        for t in workers:
            t.join()
            worker_stdout_bufs[self.cur_stage].close()
            worker_stderr_bufs[self.cur_stage].close()
            self.cur_stage = self.all_stages.pop(0)
            #self.report_module_progress('-MODULE SHUTDOWN-', self.cur_stage)
            #print '%s has completed its tasks!' % t.getID()
        # Save output to appropriately and make the manifest
        stage_results = []

        
        eval_results = self.config.getTerminalStage() == STAGE_INDEX_MAP['import'] or self.config.getTerminalStage() == STAGE_INDEX_MAP['identify']
        _stage = 0
        hits = 0
        misses = 0
        item_count = 0
        for q in stage_qs:
            stage_results.insert(0, [])
            while not q.empty():
                elem = q.get()
                if elem == None:
                    stage_results[0].append(elem)
                    #q.get()
                    #stage_results[0].append(e)
                    #e = q.get()
                elif _stage == self.config.getTerminalStage()+1:
                    (e, n) = elem
                    item_count += 1
                    if eval_results and 'evaluated' not in e:
                        if 'identity' in e:
                            hits += 1
                        else:
                            misses += 1
                        e['evaluated'] = True
                    stage_results[0].append((e, n))
            _stage += 1
        stage_results.reverse()
    
        if eval_results:
            self.set_subtitle(' %s - %d hits, %d misses' % (self.config.session, hits, misses))
        else:
            self.set_subtitle(' %s - %d items processed' % (self.config.session, item_count))

        self.clear_console()

        with open(self.config.manifest_path, "w") as manifest: 
            pickle.dump(dict(enumerate(stage_results)), manifest)

        self.config.saveConfig()

if __name__ == '__main__':
    config = MuseConfig(ParseArgs())
    if config.compile_sessions:
        compiler = MuseSessionCompiler(config)
        compiler.run()
    else:
        muse = Muse(config)
        muse.run()
