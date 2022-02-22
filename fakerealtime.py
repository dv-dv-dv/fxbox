def main():
    import wave
    import numpy as np
    import time
    
    ##user imports
    import config as cfg
    import compressor_cy as compressor
    import convolver_cy as convolver    
    # import compressor as compressor
    # import convolver as convolver
    
    wfi = wave.open('sjvoicesamp16.wav', 'rb')
    wfo = wave.open('sjvoicesamp16_pyout.wav', 'wb')
    
    wfo.setnchannels(cfg.channels)
    wfo.setsampwidth(cfg.bytes_per_channel)
    wfo.setframerate(cfg.samplerate)
    in_data = B'\x00\x00\x00'
    out_data = B'\x00\x00\x00'
    in_data = wfi.readframes(cfg.buffer)
    comp = compressor.Compressor2()
    conv = convolver.Convolver2('impulses/IMPSpring04.wav')
    count = 0
    
    print("starting fake real time...")
    start = time.clock_gettime_ns(0)
    while (len(in_data) == cfg.buffer*4)&(count < 999999999):
        x = np.frombuffer(in_data, dtype=np.int16)
        x = x.reshape(len(in_data)//(cfg.channels*cfg.bytes_per_channel),cfg.channels)
        # processing goes here
        # y = comp.compress(x)
        test1 = x
        test1 = conv.convolve(test1)
        test1 = comp.compress(test1)
        # y = np.stack((test1, test1), axis=1)
        
        y = test1
        if count==255:
            asdf = 123
        # print(count)
        # processing ends here
        out_data = y.tobytes()
        # write out_data to output wav
        # get new data from input wav file
        wfo.writeframes(out_data)
        in_data = wfi.readframes(cfg.buffer)
        count = count + 1

    wfi.close()
    wfo.close()
    end = time.clock_gettime_ns(0)
    print("fake real time finished in ", (end - start)/10**9, " seconds")
    
if __name__ == "__main__":
    main()