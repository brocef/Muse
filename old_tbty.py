import argparse
import os
from math import log
from difflib import SequenceMatcher

SCORE_BASE = 1.1

def nilog(x):
    return -1.0 * log(1.0-x, SCORE_BASE)

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

STAGES = ('search', 'video', 'extract', 'identify', 'import', 'exit') 
STAGE_INDEX_MAP = {stage:index for (index, stage) in list(enumerate(STAGES))}

DEFAULT_HOME_DIR = '%s/TBTY' % os.getcwd()

def ParseQuery(query):
    if len(query) == 0:
        err = 'The query cannot be an empty string!'
        raise argparse.ArgumentTypeError(err)
    
    
    (query, query_type, max_results) = query.split(':')

def ParseArgs():
    parser = argparse.ArgumentParser(prog='TBTY')
    parser.add_argument('-S --start-stage', dest='initial_stage', choices=STAGES, default=STAGES[0],
            help='The stage %(prog)s should start with (default %(default)r)')
    parser.add_argument('-F --final-stage', dest='terminal_stage', choices=STAGES, default=STAGES[len(STAGES)-2],
            help='The stage %(prog)s should finish with (default %(default)s)')
    parser.add_argument('-D --home-dir', dest='home_dir', metavar='HOME_DIR_PATH', default=DEFAULT_HOME_DIR,
            help='The directory in which TBTY stage folders are created (default %(default)s)')
    parser.add_argument('queries', nargs='+', metavar='QUERY:{Artist,Track,Album,*}:MAX_N_RESULTS',
            type=ParseQuery, help='Search queries to use when scraping YouTube. You can also improve accuracy by tagging your search terms like %(metavar)s, ex: RZA:Artist:10 for a maximum of 10 candidate tracks of the Artist, RZA. Big Boi:*:10 for any video from the query Big Boi.')



    args = parser.parse_args()
    print args
    if STAGE_INDEX_MAP[args.initial_stage] > STAGE_INDEX_MAP[args.terminal_stage]:
        raise TypeError('The final stage cannot happen before the start stage!')
    return args

class TBTYConfig(object):
    def __init__(self, parsed_args):
        self.initial_stage = STAGE_INDEX_MAP[parsed_args.initial_stage]
        self.terminal_stage = STAGE_INDEX_MAP[parsed_args.terminal_stage]+1
        self.home_dir = parsed_args.home_dir
        self._createSystemResources()

    def _createSystemResources(self):
        if os.path.exists(self.home_dir):
            if not os.path.isdir(self.home_dir):
                raise IOError('Provided home directory already exists, but not as a directory')
        else:
            os.mkdir(self.home_dir)

    def getInitialStage(self):
        return self.initial_stage
    
    def getTerminalStage(self):
        return self.terminal_stage

    def getHomeDirectoryPath(self):
        return self.home_dir

class TBTY(object):
    def __init__(self, config):
        self.config = config

    def run(self):
        prev = None
        for cur_stage in STAGES[self.config.getInitialStage():self.config.getTerminalStage()+1]:
            result = {
                'search': lambda x: x,
                'video': lambda x: x,
                'extract': lambda x: x,
                'identify': lambda x: x,
                'import': lambda x: x,
                'exit': lambda x: x
            }[STAGE_INDEX_MAP[self.cur_stage]](prev)
            prev = result

if __name__ == '__main__':
    print 'hi'
    config = TBTYConfig(ParseArgs())
    tbty = TBTY(config)
    tbty.run()
