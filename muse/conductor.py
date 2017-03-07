import os
import threading
import re
from Queue import Queue, Empty
import random
import time
import datetime
import pickle
from StringIO import StringIO

from muse import STAGES, STAGE_INDEX_MAP
from config import Config, ParseArgs
from worker import Worker, WORKER_TYPES, WORKER_TYPE_MAP
from query import QUERY_TYPES, query
from scout import Scout
from doctor import Doctor
from agent import Agent
from caravan import Caravan
from friend import Friend
from consoleui import ConsoleUI
from sessioncompiler import SessionCompiler

'''
Charged with the construction of worker pools and facilitate the transport of
information between workers.

Input is the initial configuration, reporting interface (UI)
Output is the result of the app execution after completion
  or the state of the app when terminated prematurely.
'''
class Conductor(object):
    def __init__(self, config):
        self.config = config

    '''
    Run is responsible for the entire application lifecycle.
    '''
    def run(self):
        workers = []












class OldConductor(object):
    def __init__(self, config):
        self.config = config
        self.cur_pct = 0.0
        self.all_stages = range(0, config.getTerminalStage()+2)
        self.cur_stage = 0
        self.authors = ['NIT'] + list(WORKER_TYPES)
        self.author_index_map = dict((v, k) for k, v in dict(enumerate(self.authors)).iteritems())
        self.progs = [0 for x in self.authors]
        self.status_strs = ['' for x in self.authors]
        self.ui = ConsoleUI(self.authors, 10, viewport_width=60, dx=(0, 10), dy=(0, 2))
        self.set_title('Muse')
        self.set_subtitle(' ' + self.config.session)
        for a in xrange(0, len(self.authors)):
            self.report_module_progress(self.status_strs[a], a)
            self.report_module_percent(0.0, a)
        self.set_footer('< :: >         < :: >', 'f_t_f')

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

