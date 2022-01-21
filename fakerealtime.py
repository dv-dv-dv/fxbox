import wave
import numpy as np

##user imports
import settings as cfg
import compressor as comp

wfi = wave.open('sjvoicesamp16.wav', 'rb')
wfo = wave.open('sjvoicesamp16_pyout.wav', 'wb')

wfo.setnchannels(cfg.channels)
wfo.setsampwidth(cfg.bytes_per_channel)
wfo.setframerate(cfg.samplerate)

in_data = B'\x00\x00\x00'
# play stream (3)
out_data = np.zeros((1,2), dtype='i2')
no_frames1 =  wfi.getnframes()
no_frames2 = 0
while len(in_data) > 0:
    no_frames2 +=(len(in_data)/4)
    in_data = wfi.readframes(cfg.buffer)
    x = np.frombuffer(in_data, dtype=np.int16)
    x = x.reshape(len(in_data)/(cfg.channels*cfg.bytes_per_channel),cfg.channels)
    #processing goes here
    y=comp.compressor(x)
    #processing ends here
    out_data = y
    out_datab = out_data.tostring()
    wfo.writeframes(out_datab)

wfi.close()
wfo.close()