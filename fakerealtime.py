def main():
    import wave
    import numpy as np
    
    ##user imports
    import config as cfg
    import compressor
    import convolver
    
    wfi = wave.open('guitar_sample16.wav', 'rb')
    wfo = wave.open('guitar_sample16_pyout.wav', 'wb')
    
    wfo.setnchannels(cfg.channels)
    wfo.setsampwidth(cfg.bytes_per_channel)
    wfo.setframerate(cfg.samplerate)
    
    in_data = B'\x00\x00\x00'
    out_data = B'\x00\x00\x00'
    in_data = wfi.readframes(cfg.buffer)
    comp = compressor.Compressor()
    conv = convolver.Convolver()
    count = 0
    test = 100
    while len(in_data) == cfg.buffer*4:
        x = np.frombuffer(in_data, dtype=np.int16)
        x = x.reshape(len(in_data)//(cfg.channels*cfg.bytes_per_channel),cfg.channels)
        # processing goes here
        # y = comp.compress(x)
        test = conv.convolve(x[:,1])
        y= np.transpose(np.concatenate((test,test)).reshape(2,-1))
        # processing ends here
        out_data = y.tobytes()
        # write out_data to output wav
        # get new data from input wav file
        wfo.writeframes(out_data)
        in_data = wfi.readframes(cfg.buffer)
        count = count + 1

        
    wfi.close()
    wfo.close()
    print (count)
if __name__ == "__main__":
    main()