def main():
    import wave
    import numpy as np
    import time
    
    # user imports
    import config as cfg
    import compressor
    import convolver
    import equalizer
    
    in_file = 'guitar_sample16'
    wfi = wave.open(in_file + '.wav', 'rb')
    wfo = wave.open(in_file + '_pyout.wav', 'wb')
    wave_input_blength = wfi.getnframes()//cfg.buffer_size
    wfo.setnchannels(cfg.channels)
    wfo.setsampwidth(cfg.bytes_per_channel)
    wfo.setframerate(cfg.samplerate)
    in_data = wfi.readframes(cfg.buffer_size)
    
    # comp = compressor.Compressor()
    # limiter = compressor.Compressor(threshold=-6, ratio=999, knee_width=0, attack=0.001, release=0.001, rms=True)
    # conv = convolver.Convolver()
    equal = equalizer.Equalizer()
    count = 0
    
    print("buffer size is", cfg.buffer_size)
    print("starting fake real time...")
    start1 = time.perf_counter()
    exempt_time = 0
    while (len(in_data) == cfg.buffer_size*4):
        x = np.frombuffer(in_data, dtype=np.int16)
        x = x.reshape(cfg.buffer_size, 2)
        # processing goes here
        test1 = x/2**15
        # test1 = comp.compress(test1)
        test1 = equal.equalize(test1)
        # test1 = conv.convolve(test1)
        # if count == int(wave_input_blength*2/4):
            # conv.update_params(imp_number=3, dry=0.5)
        if np.max(test1) > 1:
            print("clipping!")
        # processing ends here
        y = (test1*2**15).astype(np.int16)
        out_data = y.tobytes()
        exempt_time -= time.perf_counter()
        wfo.writeframes(out_data)
        in_data = wfi.readframes(cfg.buffer_size)
        exempt_time += time.perf_counter()
        count = count + 1
    
    end = time.perf_counter()
    wfi.close()
    wfo.close()
    print("fake real time finished in", round(end - start1 - exempt_time, 3), "seconds")
    print("looped", count, "times")
    
if __name__ == "__main__":
    main()