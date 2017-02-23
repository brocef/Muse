import os
import re
import pickle
from Queue import Queue

def _is_session(session_name_re, sessions_dir, s):
    if session_name_re.match(s):
        s_path = os.path.join(sessions_dir, s)
        if os.path.isdir(s_path):
            return True
    return False

class MuseSessionCompiler:
    def __init__(self, config):
        self.config = config
        self.session_name_re = re.compile(r'[A-Z]{3}\d{1,3}_\d+')

    def run(self):
        s_filt = lambda s: _is_session(self.session_name_re, self.config.sessions_dir, s)
        sessions = map(lambda s: os.path.join(self.config.sessions_dir, s), filter(s_filt, os.listdir(self.config.sessions_dir)))
        try:
            stat_hist_fd = open(self.config.stat_hist_path, 'r')
            stat_hist = pickle.load(stat_hist_fd)
            stat_hist_fd.close()
        except Exception:
            stat_hist = []
        init_len = len(stat_hist)
        for s in sessions:
            manifest_path = os.path.join(s, 'manifest')
            if os.path.isfile(manifest_path):
                try:
                    need_update = False
                    stage_imports = None
                    with open(manifest_path, 'r') as manifest:
                        stage_imports = pickle.load(manifest)
                        if len(stage_imports[5]) > 0:
                            while len(stage_imports[5]) > 0:
                                r = stage_imports[5].pop()
                                stat_hist.append(r)
                                need_update = True
                    if need_update:
                        with open(manifest_path, 'w') as manifest:
                            pickle.dump(stage_imports, manifest)
                except Exception as e:
                    print(e)
                    continue
        stat_hist_fd = open(self.config.stat_hist_path, 'w')
        pickle.dump(stat_hist, stat_hist_fd)
        stat_hist_fd.close()
        print('Compiled %d Results' % (len(stat_hist) - init_len))
