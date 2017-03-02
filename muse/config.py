import os
import os.path

STAGES = ('search', 'video', 'extract', 'identify', 'import')
DEFAULT_HOME_DIR = os.path.join(os.getcwd(), 'Muse')
DEFAULT_SESSIONS_DIR = os.path.join(DEFAULT_HOME_DIR, 'Sessions')

DEFAULT_CONFIG = {
    'home_dir': DEFAULT_HOME_DIR,
    'sessions_dir': DEFAULT_SESSIONS_DIR,
    'terminal_stage': STAGES[len(STAGES)-1]
}

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


