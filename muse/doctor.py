import worker
import os
import subprocess
import time
import sys
import re
import math

class Doctor(worker.Worker):
    def process(self, yt_result_pc, prog_cb):
        if yt_result_pc['CVN'] == 'download_success':
            mp4n = yt_result_pc['mp4_path']
            mp3n = yt_result_pc['mp3_path']
            mp4n_size_bytes = os.path.getsize(mp4n)
            prog_cb('Starting Audio Extraction')
            ffmpeg = subprocess.Popen(['ffmpeg', '-loglevel', 'quiet', '-y', '-stats', '-i', mp4n, '-vn', '-sn', '-c:a', 'mp3', '-ab', '192k', mp3n], stderr=subprocess.PIPE)
            while ffmpeg:
                chunk = ffmpeg.stderr.read(1024)
                #print chunk
                if chunk == '' and ffmpeg.poll() is not None:
                    break
                if chunk:
                    last_size = None
                    for last_size in re.finditer(r'size=\s+(\d+)(\w+)\s+', chunk):
                        (size_str, size_unit) = last_size.groups()
                        size = float(size_str)
                        if size_unit == 'kB':
                            size *= pow(10, 3)
                        elif size_unit == 'MB':
                            size *= pow(10, 6)
                        elif size_unit == 'GB':
                            size *= pow(10, 9)
                        else:
                            size *= pow(10, 3) #???
                        pct = math.atan(3.0*(size+1)/(mp4n_size_bytes+1))*100.0/math.pi*2
                        prog_cb('Extracting Audio (%2.1f%%)' % pct)
            os.remove(mp4n)
            subprocess.call(['eyeD3', '-l', 'error', '-Q', '--remove-all', mp3n], stdout=subprocess.PIPE, stderr=subprocess.PIPE)# stdout=open(mp3n[:-4], "w"), stderr=open(mp3n[:-4]+"err", "w"))
            del yt_result_pc['mp4_name']
            del yt_result_pc['mp4_path']
            yield yt_result_pc
        else:
            yield yt_result_pc
