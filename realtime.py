import pyaudio
import time
import numpy as np

#user imports
import settings as cfg
import compressor as comp


p = pyaudio.PyAudio()
 
print(p.get_default_host_api_info())
no_indexes = p.get_device_count()
for x in range(0, no_indexes):
     print(p.get_device_info_by_index(x))
 
 
def callback(in_data, frame_count, time_info, status):
    x = np.frombuffer(in_data, dtype=np.int16)
    x = x.reshape(len(in_data)/(cfg.channels*cfg.bytes_per_channel),cfg.channels)
    #processing goes here

    y=comp.compressor(x)
    #processing ends here
    out_data = y.tostring()
    return (out_data, pyaudio.paContinue)
 
stream = p.open(format=pyaudio.paInt16,
                channels=cfg.channels,
                input_device_index = 0,
                output_device_index = 0,
                rate=cfg.samplerate,
                output=True,
                input=True,
                frames_per_buffer=cfg.buffer,
                stream_callback=callback)
 
stream.start_stream()
while stream.is_active():
    print('going...')
    time.sleep(1)
stream.stop_stream()
p.terminate()