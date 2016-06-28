import argparse
import os
import socket
import threading
from math import log
from difflib import SequenceMatcher
import re
from Queue import Queue

from TBTYWorker import TBTYWorker, WORKER_TYPES, WORKER_TYPE_MAP, COMMANDS
from TBTYQuery import QUERY_TYPES, TBTYQuery
from TBTYScout import TBTYScout
from TBTYDoctor import TBTYDoctor
from TBTYAgent import TBTYAgent
from TBTYCaravan import TBTYCaravan
from TBTYFriend import TBTYFriend

SCORE_BASE = 1.1

def nilog(x):
    return -1.0 * log(1.0-x, SCORE_BASE)

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

STAGES = ('search', 'video', 'extract', 'identify', 'import')
STAGE_CONSTRS = (
            lambda config: TBTYScout(config),
            lambda config: TBTYCaravan(config),
            lambda config: TBTYDoctor(config),
            lambda config: TBTYAgent(config),
            lambda config: TBTYFriend(config)
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
    parser.add_argument('-H --host', dest='host', metavar='HOSTNAME', default='localhost',
            help='The hostname where to host TBTY')
    parser.add_argument('-P --port', dest='port', metavar='PORT', default=0xFEAF,
            help='The port where to host TBTY')
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
        self.queries = parsed_args.queries
        self.server_addr = (parsed_args.host, parsed_args.port)
        self._createSystemResources()
        if self.resume == None:
            self.resume = False
            self._loadConfig(self.resume)

    def _loadConfig(self):
        pass

    def _createSystemResources(self):
        if os.path.exists(self.home_dir):
            if not os.path.isdir(self.home_dir):
                raise IOError('Provided home directory already exists, but not as a directory')
        else:
            os.mkdir(self.home_dir)

    def doesSessionExist(self, session):
        return os.path.exists(os.path.join(os.home_dir, session))

    def getInitialStage(self):
        return self.initial_stage
    
    def getTerminalStage(self):
        return self.terminal_stage

    def getHomeDirectoryPath(self):
        return self.home_dir

    def getServerAddress(self):
        return self.server_addr

    def stringify(self):
        return '[%s, %s]=>%s\n%s' % (STAGES[self.initial_stage], STAGES[self.terminal_stage], self.home_dir, str(map(lambda x: x.stringify(), self.queries)))

def SocketToQueue(conn, q):
    while conn:
        data = conn.recv(1024)
        if not data:
            conn.close()
            return
        q.put(data.strip())

class TBTYSupervisor:
    def __init__(self, worker_type, conn_addr):
        self.w_type = worker_type
        self.conn = conn_addr[0]
        self.addr = conn_addr[1]

MAX_CXNS = 5
class TBTY(object):
    def __init__(self, config):
        self.config = config
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        # Prepare the server socket
        self._server.bind(self.config.getServerAddress())
        self._server.listen(6)
        
        # Create thread(s) for each stage
        stg_threads = map(lambda t: t(self.config), STAGE_CONSTRS[self.config.getInitialStage():self.config.getTerminalStage()+1])
        map(lambda t: t.start(), stg_threads)
        # Map client threads to stages??
        #stg_map = dict(zip(STAGES[self.config.getInitialStage():self.config.getTerminalStage()+1], stg_threads))

        # Create client connection mapping and create a set of 'listener' threads
        #   which simply wait for socket data and once it is available it alerts
        #   this thread with a semaphore/lock/whatever
        q = Queue()
        stg_listeners = dict()
        stg_cxns = dict()
        t_count = 0

        # Fix buffering issue here where the pipe has no line delimiter to break up
        # messages which collect in the socket buffer

        while t_count < len(stg_threads):
            conn, addr = self._server.accept()
            who = conn.recv(1024)
            if not who:
                break
            who = who.strip()
            (w_type, msg) = TBTYWorker.parse_msg(who)
            stg_cxns[w_type] = (conn, addr)
            t = threading.Thread(target=lambda: SocketToQueue(conn, q))
            stg_listeners[w_type] = t
            t.start()
            t_count += 1
    
        # Handle information passage, usually where the client report their
        #   findings/progress to the server to alert the next stage's thread with
        #   the appropriate info
        for t in WORKER_TYPES:
            stg_cxns[t][0].sendall(t+'\n')
        i = 0
        while i < len(stg_threads):
            g = q.get()
            print 'Recvd: %s' % g
            i += 1

        for t in WORKER_TYPES:
            stg_cxns[t][0].sendall(COMMANDS['kill']+'\n')

        print 'Closing all sockets'
        map(lambda s: s[0].close(), stg_cxns.values())

        # Join my folding right on a sorted array of client threads,
        #   where the first stage is joined with first, assuring that the job is
        #   fully completed, in order, before shutoff
        
        print 'Joining on stage threads'
        for t in stg_threads:
            t.join()

        # Shutoff
        print 'Shutting down...'




#        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        client.connect(self._server_addr)
#        client.sendall('Hello, world')
#        client.close()
#        t.join()

#        prev = None
#        for cur_stage in STAGES[self.config.getInitialStage():self.config.getTerminalStage()+1]:
#            result = {
#                'search': lambda x: x,
#                'video': lambda x: x,
#                'extract': lambda x: x,
#                'identify': lambda x: x,
#                'import': lambda x: x
#            }[STAGE_INDEX_MAP[cur_stage]](prev)
#            prev = result


if __name__ == '__main__':
    config = TBTYConfig(ParseArgs())
    tbty = TBTY(config)
    tbty.run()
