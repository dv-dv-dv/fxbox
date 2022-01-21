import pyaudio
import time
import numpy as np
CHUNK = 1024
BITS = np.int16
 
CHANNELS = 2
BYTES_PER_CHANNEL = 2                                                                                                                                                                                                        
RATE = 44100
if BITS == np.int16:
    BYTES_PER_CHANNEL = 2
elif BITS == np.int24:
    BYTES_PER_CHANNEL = 3
ALENGTH = CHANNELS*BYTES_PER_CHANNEL*CHUNK
p = pyaudio.PyAudio()
 
print(p.get_default_host_api_info())
no_indexes = p.get_device_count()
for x in range(0, no_indexes):
     print(p.get_device_info_by_index(x))
 
 
def callback(in_data, frame_count, time_info, status):
    #Get data into a usable format
    data2 = np.frombuffer(in_data, dtype=np.int16)
    data2 = data2.reshape(CHUNK,CHANNELS)
    #processing goes here
    
    #Get data back into buffer and send to output stream
    data = data2.tostring()
    out_data = data
    return (out_data, pyaudio.paContinue)
 
stream = p.open(format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=RATE,
                output=True,
                input=True,
                frames_per_buffer=CHUNK,
                stream_callback=callback)
 
stream.start_stream()
while stream.is_active():
    print('going...')
    time.sleep(1)
stream.stop_stream()
p.terminate()