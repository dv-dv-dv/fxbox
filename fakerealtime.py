def main():
    import wave
    import numpy as np
    import time
    
    ##user imports
    import config as cfg
    import compressor
    import convolver
    import equalizer
    
    in_file = 'guitar_sample16'
    wfi = wave.open(in_file + '.wav', 'rb')
    wfo = wave.open(in_file + '_pyout.wav', 'wb')
    
    wfo.setnchannels(cfg.channels)
    wfo.setsampwidth(cfg.bytes_per_channel)
    wfo.setframerate(cfg.samplerate)
    in_data = wfi.readframes(cfg.buffer)
    
    comp = compressor.Compressor()
    conv = convolver.Convolver(impulse_number=1)
    equal = equalizer.Equalizer()
    count = 0
    
    print("buffer size is", cfg.buffer)
    print("starting fake real time...")
    start1 = time.perf_counter()
    exempt_time = 0
    while (len(in_data) == cfg.buffer*4):
        x = np.frombuffer(in_data, dtype=np.int16)
        x = x.reshape(len(in_data)//(cfg.channels*cfg.bytes_per_channel),cfg.channels)
        # processing goes here
        test1 = x/2**15
        test1 = comp.compress(test1)
        test1 = equal.equalize(test1)
        test1 = conv.convolve(test1)
        if(np.max(test1)>1):
            print("clipping!")
        # processing ends here
        y = (test1*2**15).astype(np.int16)
        out_data = y.tobytes()
        exempt_time -= time.perf_counter()
        wfo.writeframes(out_data)
        in_data = wfi.readframes(cfg.buffer)
        exempt_time += time.perf_counter()
        count = count + 1
    
    end = time.perf_counter()
    wfi.close()
    wfo.close()
    print("fake real time finished in", round(end - start1 - exempt_time, 2), "seconds")
    
if __name__ == "__main__":
    main()