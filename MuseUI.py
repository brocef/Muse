from __future__ import print_function
from blessings import Terminal
import sys
import threading
import random
import time
import MuseWorker 

WORKER_TYPES = ['NIT'] + list(MuseWorker.WORKER_TYPES)

_print = lambda s: print(s, end='')

class MuseUI:
    def __init__(self, viewport_height, viewport_width=40, dx=(1, 10), dy=(0,2)):
        self.height = viewport_height
        self.width = viewport_width
        self.term = Terminal()
        self.lines = ['' for i in xrange(0, viewport_height)]
        self.percents = [None for i in xrange(0, viewport_height)]
        self.print_lock = threading.Lock()
        self.viewport = (dx, dy)
        self.dx = dx
        self.dy = dy
        self.calculateEffectiveViewport()
        self._count = 0
        self.ACTIVE_COLORS = (self.term.cyan, self.term.yellow, self.term.magenta, self.term.blue, self.term.green, self.term.red)
        self.WORKER_NAME_STRS = ['%s' % self.ACTIVE_COLORS[worker](WORKER_TYPES[worker]) for worker in xrange(0, len(WORKER_TYPES))]
        self.worker_ids = [None for i in xrange(0, self.height)]

        self.prog_format = '%3d%%[%s%s]'
        self.prog_len = 16
        self.worker_format = '[%s] '
        self.worker_len = 6

        self.line_len = self.eff_width - (self.prog_len + self.worker_len)
        self.line_format = '%-' + str(self.line_len) + 's%+16s'

        self.final_format = '%s%s'# % (self.worker_format, self.line_format, self.prog_format)

    def calculateEffectiveViewport(self):
        (dx_min, dx_max) = self.dx
        (dy_min, dy_max) = self.dy

        self.eff_width = None
        self.eff_viewport = [dx_min, dy_min]
        if self.term.height >= self.height + dy_max * 2:
            self.eff_viewport[1] = dy_max
        elif self.term.height <= self.height + dy_min * 2:
            self.eff_viewport[1] = dy_min
        else:
            self.eff_viewport[1] = (self.term.height - self.height) / 2
        
        if self.term.width >= self.width + dx_max * 2:
            self.eff_viewport[0] = dx_max
            self.eff_width = self.term.width - dx_max * 2
        elif self.term.width <= self.width + dx_min * 2:
            self.eff_viewport[0] = dx_min
            self.eff_width = self.term.width - dx_min * 2
        else:
            self.eff_viewport[0] = (self.term.width - self.width) / 2
            self.eff_width = self.term.width - self.eff_viewport[0] * 2
        self.eff_viewport = tuple(self.eff_viewport)

    def getTerm(self):
        return self.term

    def prepareTerm(self):
        (dx, dy) = self.eff_viewport
        for i in xrange(0, self.height+2*dy):
            print('')

    def setProgress(self, line, percent):
        self.percents[line] = percent

    def setLineText(self, line, text, worker_id=None):
        self.lines[line] = text
        self.worker_ids[line] = worker_id

    def refresh(self):
        self.print_lock.acquire()
        (dx, dy) = self.eff_viewport
        with self.term.location():
            _print(self.term.move_up * (self.height + dy))
            _print(self.term.clear_eos)
            for i in xrange(0, self.height):
                _print(' ' * dx)
                using_prog = self.percents[i] != None
                if using_prog:
                    prog = self.prog_format % (self.percents[i], '=' * (self.percents[i]/10), ' ' * (10-(self.percents[i]/10)))
                else:
                    prog = ''
                line = self.lines[i]
                worker_id = self.worker_ids[i]
                len_lim = self.line_len + self.worker_len if worker_id == None else self.line_len
                len_lim += 0 if using_prog else self.prog_len
                if len(line) > len_lim:
                    line = line[:len_lim]
                if worker_id == None:
                    worker = ''
                else:
                    worker = self.worker_format % self.WORKER_NAME_STRS[worker_id]
                if using_prog:
                    line_w_prog = self.line_format % (line, prog)
                else:
                    line_w_prog = line
                _print(self.final_format % (worker, line_w_prog))
                _print(' ' * dx)
                _print(self.term.move_down)
                self.term.location(x=0)
            _print(self.term.move_down * dy)
            self._count += 1
        sys.stdout.flush()
        self.print_lock.release()

ui = MuseUI(9, viewport_width=60, dx=(0, 10), dy=(0, 2))
ui.setLineText(0, 'Fuck yeah boi! ' * 10)
ui.setLineText(1, 'Made by f_t_f')
for i in xrange(0, len(WORKER_TYPES)):
    status = 'STATUS: %s' % ('Unknown')
    ui.setLineText(i+2, status)
    ui.setProgress(i+2, 0)
ui.setLineText(2+len(WORKER_TYPES), 'Footer')
ui.prepareTerm()
ui.refresh()
time.sleep(1)

for i in xrange(0, 21):
    ui.setLineText(0, 'Real count %d' % i * 10)
    for j in xrange(0, len(WORKER_TYPES)):
        if i <= 10:
            ui.setProgress(j+2, i*10)
        else:
            ui.setProgress(j+2, 200-i*10)
        ui.setLineText(j+2, 'At iteration %d' % (50*i) * 10, worker_id=j)
    ui.refresh()
    time.sleep(0.25)

