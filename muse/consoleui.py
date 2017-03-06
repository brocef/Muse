from __future__ import print_function
from blessings import Terminal
import sys
import threading
import random
import time
import worker

#WORKER_TYPES = ['NIT'] + list(worker.WORKER_TYPES)

_print = lambda s: print(s, end='')

class ConsoleUI:

# BEGIN WRAPPER FUNCTIONS
    def setProgress(self, line, percent):
        self.setProgress(line, percent)
        self.refresh()

    def setLineText(self, line, text, worker_id=None):
        self.setLineText(line, text, worker_id=worker_id)
        self.refresh()

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
        self.setLineTextCustom(0, title, 'center')
        self.refresh()

    def set_subtitle(self, text):
        self.setLineText(1, text)

    def set_footer(self, firstline, secondline):
        self.setLineTextCustom(8, firstline, 'center')
        self.setLineTextCustom(9, secondline, 'center')
        self.refresh()

    def clear_console(self):
        self.clear()
        self.refresh()
# END WRAPPER FUNCTIONS

    def __init__(self, module_names, viewport_height, viewport_width=40, dx=(1, 10), dy=(0,2)):
        self.MODULES = module_names
        self.height = viewport_height
        self.width = viewport_width
        self.term = Terminal()
        self.lines = ['' for i in xrange(0, viewport_height)]
        self.percents = [None for i in xrange(0, viewport_height)]
        self._lock = threading.Lock()
        self.viewport = (dx, dy)
        self.dx = dx
        self.dy = dy
        self.calculateEffectiveViewport()
        self._clear = False
        self._count = 0
        self._has_prepped = False
        assert(len(module_names) == 6)
        self.ACTIVE_COLORS = (self.term.cyan, self.term.yellow, self.term.magenta, self.term.blue, self.term.green, self.term.red)
        self.WORKER_NAME_STRS = ['%s' % self.ACTIVE_COLORS[worker](self.MODULES[worker]) for worker in xrange(0, len(self.MODULES))]
        self.worker_ids = [None for i in xrange(0, self.height)]

        self.prog_format = '%3d%%[%s%s]'
        self.err_prog_format = '%3s%%[%s%s]'
        self.custom_prog_format = '%4s[%-10s]'
        self.prog_len = 16
        self.worker_format = '[%s] '
        self.worker_len = 6

        self.line_len = self.eff_width - (self.prog_len + self.worker_len)
        self.line_format = '%-' + str(self.line_len) + 's%+16s'

        self.final_format = '%s%s'# % (self.worker_format, self.line_format, self.prog_format)
        self.prepareTerm()

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
        self._lock.acquire()
        (dx, dy) = self.eff_viewport
        for i in xrange(0, self.height+2*dy):
            print('')
        self._has_prepped = True
        self._lock.release()

    def setProgress(self, line, percent):
        if line >= len(self.percents):
            print(line)
            print(self.percents)
            sys.exit(1)
        self._lock.acquire()
        if percent == None:
            self.percents[line] = None
        else:
            if type(percent) == float or type(percent) == int:
                self.percents[line] = percent*100.0
            else:
                self.percents[line] = percent
        self._lock.release()

    def setLineTextCustom(self, line, text, custom):
        if custom == 'center':
            text = text[:min(len(text), self.eff_width)]
            dw = float(self.eff_width - len(text))
            left = int(0.5 + dw / 2.0)
            right = int(dw / 2.0)
            text = ' ' * left + text + ' ' * right

        self.setLineText(line, text)

    def setLineText(self, line, text, worker_id=None):
        self._lock.acquire()
        self.lines[line] = text
        self.worker_ids[line] = worker_id
        self._lock.release()

    def clear(self):
        self._lock.acquire()
        self._clear = True
        self._lock.release()

    def refresh(self):
        self._lock.acquire()
        (dx, dy) = self.eff_viewport
        with self.term.location():
            _print(self.term.move_up * (self.height + dy))
            for i in xrange(0, self.height):
                if self._clear:
                    continue
                _print(' ' * dx)
                using_prog = self.percents[i] != None
                if using_prog:
                    if type(self.percents[i]) == float or type(self.percents[i]) == int:
                        if self.percents[i] < 0.0:
                            prog = self.err_prog_format % ('???', '!! %01.2f !!' % (self.percents[i] / -100.0), '')
                        else:
                            prog = self.prog_format % (self.percents[i], '=' * int(self.percents[i]/10), ' ' * (10-int(self.percents[i]/10)))
                    else:
                        prog = self.custom_prog_format % self.percents[i]
                    prog = prog[:min(len(prog), self.prog_len)]
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
        self._clear = False
        sys.stdout.flush()
        self._lock.release()

