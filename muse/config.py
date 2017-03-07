import os
import os.path
import re
import argparse

from muse import STAGES

DEFAULT_HOME_DIR = os.path.join(os.getcwd(), 'Muse')
DEFAULT_SESSIONS_DIR = os.path.join(DEFAULT_HOME_DIR, 'Sessions')

DEFAULT_CONFIG = {
    'home_dir': DEFAULT_HOME_DIR,
    'sessions_dir': DEFAULT_SESSIONS_DIR,
    'terminal_stage': STAGES[len(STAGES)-1]
}
'''
The Config object will define many key parameters which guide application
functionality. These properties are derived from several sources, with the
following hierarchy (as the same property may appear in multiple sources):
    1. User arguments from the command-line
    2. Properties from the configuration file (config_path)
    3. Default properties as defined in this file (DEFAULT_CONFIG)

Once the Config object is initialized, it will offer the following "getter"
functions for important properties:
    -getMode()
        -isModeDiscover()
        -isModeResume()
        -isModeCompile()
    -getTerminalStage()
    !getInitialStage()
    -getConfigPath()
    -getSessionName()
    -getSessionDir()
    -getHomeDir()
    -
'''
class Config(object):
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
        Config._ensureDirCreation(self.home_dir)
        Config._ensureDirCreation(self.sessions_dir)
        if self.cur_session_dir:
            Config._ensureDirCreation(self.cur_session_dir)
            Config._ensureDirCreation(self.session_unk_dir)
        if self.mode == 'resume':
            Config._ensureFileExists(self.manifest_path)
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
        return query(clean_query, terms, num)
    else:
        err = 'The query must be similar to the following form: {Queen:Artist} Lyric Videos:5'
        raise argparse.ArgumentTypeError(err)

def SafeParseQuery(query):
    try:
        return ParseQuery(query) != None
    except Exception:
        return False

'''
Muse can run in the following "modes":
    1. discover - the main function of the app which performs the end-to-end
    functionality, but may be terminated early using the -F --final-stage flag
    which allows the user to termiante Muse at an earlier stage for whatever
    reason.

    2. compile - aggregates the results of all accessible sessions including
    index information, statistics, and other related information.

    3. resume - resumes a session that was termianted before the final stage;
    which can also have its own -F --final-stage configuration such that the
    user could advance a session by one stage at a time if so desired.


Of the above modes, each can have a set of possible properties:
    discover:
        1. home_dir
        2. terminal_stage_name

    compile

    resume:
        1. terminal_stage_name
'''
def ParseArgs():
    parser = argparse.ArgumentParser(prog='Muse')
    parser.add_argument('-D --home-dir', dest='home_dir', metavar='HOME_DIR_PATH', default=DEFAULT_HOME_DIR, help='The directory in which Muse stage folders are created (default %(default)s)')
    parser.add_argument('-F --final-stage', dest='terminal_stage_name', choices=STAGES, default=STAGES[len(STAGES)-1], help='The stage %(prog)s should finish with (default %(default)s)')

    subparsers = parser.add_subparsers(dest='mode', help='Subparser help')
    discover_parser = subparsers.add_parser('discover', help='discover help')
    discover_parser.add_argument('queries', nargs='+', type=ParseQuery, metavar='Query:Count', help='Search queries to use when scraping YouTube. You can also improve accuracy of the scraper by tagging your query type in the following form: "Untagged Query Terms {Tagged Query Terms:[Artist,Track,Album]}":N. For example, "{RZA:Artist} Lyric Videos":10 would start a search for a maximum of 10 candidate tracks of the Artist, RZA, with Lyric Videos appended to the query to give better context. Big Boi:10 for any video from the query Big Boi, with no tag heuristics enabled. You may have multiple tagged terms, but they may not be nested.')

    compile_parser = subparsers.add_parser('compile', help='compile help')

    resume_parser = subparsers.add_parser('resume', help='resume help')
    resume_parser.add_argument('session', metavar='SESSION_NAME', type=str, help='Session name help')
    resume_parser.add_argument('-F --final-stage', dest='terminal_stage_name', choices=STAGES, default=STAGES[len(STAGES)-1], help='The stage %(prog)s should finish with (default %(default)s)')

    args = parser.parse_args()
    args.terminal_stage = STAGE_INDEX_MAP[args.terminal_stage_name]

    return vars(args)

