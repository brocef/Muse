import MuseWorker
import os
import subprocess

class MuseDoctor(MuseWorker.MuseWorker):
    def process(self, yt_result_pc, prog_cb):
        mp4n = yt_result_pc['mp4_name']
        mp3n = yt_result_pc['mp3_name']
        if os.path.isfile(mp4n):
            subprocess.call(['ffmpeg', '-loglevel', 'panic', '-i', mp4n, '-vn', '-sn', '-c:a', 'mp3', '-ab', '192k', mp3n])
        os.remove(mp4n)
        subprocess.call(['eyeD3', '-l', 'error', '-Q', '--remove-all', mp3n], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        yt_result_pc.pop('mp4_name')
        return [yt_result_pc]
