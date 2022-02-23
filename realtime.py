import pyaudio
import time
import numpy as np
import threading

##user imports
import config as cfg
import compressor_cy as compressor
import convolver_cy as convolver


p = pyaudio.PyAudio()

print(p.get_default_host_api_info())
no_indexes = p.get_device_count()

for x in range(0, no_indexes):
     print(p.get_device_info_by_index(x))

comp = compressor.Compressor2()
conv = convolver.Convolver2('impulses/IMPSpring04.wav')
count = 0
zeros = np.zeros((cfg.buffer, 2), dtype=np.int16)
do_conv = False
threadLock = threading.Lock()

def callback(in_data, frame_count, time_info, status):
    # threadLock.acquire()

    x = np.frombuffer(in_data, dtype=np.int16)
    y = x.reshape(-1, cfg.channels)
    # y=comp.compress(y)
    y=conv.convolve(y)
    #processing goes here


    #processing ends here
    out_data = y.tobytes()
    do_conv = True
    # threadLock.release()
    return (out_data, pyaudio.paContinue)

stream = p.open(format=pyaudio.paInt16,
                channels=cfg.channels,
                input_device_index = 2,
                output_device_index = 2,
                rate=cfg.samplerate,
                output=True,
                input=True,
                frames_per_buffer=cfg.buffer,
                stream_callback=callback)

stream.start_stream()
while stream.is_active():
    conv.convolution_worker(loop=False)
stream.stop_stream()
p.terminate()
