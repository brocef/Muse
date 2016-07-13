import MuseWorker
import os
import subprocess

class MuseFriend(MuseWorker.MuseWorker):
    def __init__(self, *args):
        super(MuseFriend, self).__init__(*args)
        self.name_hist = dict()
        self.greek_alpha = ('alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 'theta', 'iota', 'kappa', 'lambda', 'mu', 'nu', 'xi', 'omicron', 'pi', 'rho', 'sigma', 'tau', 'upsilon', 'phi', 'chi', 'psi', 'omega')
        self.greek_inv_alpha = {value: key for (key, value) in enumerate(list(self.greek_alpha))}

    def process(self, yt_result, prog_cb):
        if yt_result['CVN'] == 'download_success':
            if 'identity' in yt_result:
                prog_cb('Renaming and Importing Track')
                artist = yt_result['identity']['artist']
                track = yt_result['identity']['track']
                a_t_count = self.name_hist.get((artist, track), 0)
                self.name_hist[(artist, track)] = a_t_count + 1
                codename = '%s%s' % (self.greek_alpha[a_t_count % len(self.greek_alpha)], '' if a_t_count < len(self.greek_alpha) else (a_t_count - len(self.greek_alpha) + 1))
                better_name = '%s - %s (%s).mp3' % (artist, track, codename)
                better_path = unicode(os.path.join(self.config.cur_session_dir, better_name))
                os.rename(yt_result['mp3_path'], better_path)
                artist = yt_result['identity']['artist']
                title = yt_result['identity']['track']
                subprocess.call(['eyeD3', '-a', artist, '-b', artist, '-t', title, better_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                yt_result['mp3_name'] = better_name
                yt_result['mp3_path'] = better_path
                #subprocess.call(['beet', 'import', '-q', '-c', '-a', '-s', yt_result['mp3_path']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                prog_cb('Storing Unknown Track')
                os.rename(yt_result['mp3_path'], os.path.join(self.config.session_unk_dir, yt_result['mp3_name']))
        yield yt_result
