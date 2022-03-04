def main():
    import wave
    import numpy as np
    import time
    
    ##user imports
    import config as cfg
    import compressor_cy as compressor
    # import convolver_cy as convolver
    import convolver
    # import compressor
    
    wfi = wave.open('sjvoicesamp16.wav', 'rb')
    wfo = wave.open('sjvoicesamp16_pyout.wav', 'wb')
    
    wfo.setnchannels(cfg.channels)
    wfo.setsampwidth(cfg.bytes_per_channel)
    wfo.setframerate(cfg.samplerate)
    in_data = B'\x00\x00\x00'
    out_data = B'\x00\x00\x00'
    in_data = wfi.readframes(cfg.buffer)
    comp = compressor.Compressor2()
    conv = convolver.Convolver('impulses/IMP Spring 04')
    count = 0
    
    print("buffer size is", cfg.buffer)
    print("starting fake real time...")
    start1 = time.perf_counter()
    exempt_time = 0
    while (len(in_data) == cfg.buffer*4):
        x = np.frombuffer(in_data, dtype=np.int16)
        x = x.reshape(len(in_data)//(cfg.channels*cfg.bytes_per_channel),cfg.channels)
        # processing goes here
        test1 = x
        # test1 = comp.compress(test1)
        test1 = conv.convolve(test1)
        if(test1.shape[0]==0):
            asdf = 123
        
        # y = np.stack((test1, test1), axis=1)
        
        y = test1
        if count==255:
            asdf = 123
        # print(count)
        # processing ends here
        out_data = y.tobytes()
        # write out_data to output wav
        # get new data from input wav file
        exempt_time -= time.perf_counter()
        wfo.writeframes(out_data)
        in_data = wfi.readframes(cfg.buffer)
        exempt_time += time.perf_counter()
        count = count + 1
    
    end = time.perf_counter()
    wfi.close()
    wfo.close()
    conv.print_fft_usage()
    print("fake real time finished in", round(end - start1 - exempt_time, 2), "seconds")
    
if __name__ == "__main__":
    main()