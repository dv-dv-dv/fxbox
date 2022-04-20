def main():
    import numpy as np
    import pyaudio
    import wave
    import time
    from pynput import keyboard
    
    ##user imports
    import config as cfg
    import compressor
    import convolver
    import equalizer
    import fxboxsm
    
    in_file = '1'
    wfi = wave.open(in_file + '.wav', 'rb')
    
    p = pyaudio.PyAudio()
    
    print(p.get_default_host_api_info())
    no_indexes = p.get_device_count()
    nothing = np.zeros((cfg.buffer_size, 2), np.int16).tobytes()
    for x in range(0, no_indexes):
         print(p.get_device_info_by_index(x))
    test = True
    process = True
    master_pre_gain = 10**(cfg.master_pre_gain_db/20)
    master_post_gain = 10**(cfg.master_post_gain_db/20)
    if test==True:
        fxbox = fxboxsm.FXBox()
        comp = compressor.Compressor()
        limiter = compressor.Compressor(threshold=-12, ratio=9999, knee_width=0, attack=0.0001, release=0.01, rms=True, post_gain=0)
        conv = convolver.Convolver()
        equal = equalizer.Equalizer()
        
        def on_press(key):
            global process
            try:
                nstate = fxbox.translator(key.char)
                fxbox.new_state(nstate)
                val, state = fxbox.update_state()
                print(str(val) + "\n" + str(state))
                # compressor
                if val != None:
                    fxbox.process = False
                    if   state[0] == 1: 
                        if   state[1] == 1: 
                            comp.update_params(threshold=val)
                        elif state[1] == 2: 
                            comp.update_params(ratio=val)
                        elif state[1] == 3: 
                            comp.update_params(attack=val)
                        elif state[1] == 4: 
                            comp.update_params(post_gain=val)
                    # convolver
                    elif state[0] == 2: 
                        if   state[1] == 1: 
                            conv.update_params(imp_number=val)
                            time.sleep(0.25)
                        elif state[1] == 2: 
                            conv.update_params(wet=val, reinit=False)
                        elif state[1] == 3: 
                            conv.update_params(dry=val, reinit=False)
                        elif state[1] == 4: 
                            conv.update_params(post=val, reinit=False)
                    # equalizer
                    elif state[0] == 3: 
                        # lpf
                        if   state[1] == 1: 
                            if   state[2] == 1:
                                equal.update_params(lpf_en=val)
                            elif state[2] == 2:
                                equal.update_params(lpf_fc=val)
                            elif state[2] == 3:
                                equal.update_params(lpf_N=val)
                            elif state[2] == 4:
                                pass
                        # hpf
                        elif state[1] == 2: 
                            if   state[2] == 1:
                                equal.update_params(hpf_en=val)
                            elif state[2] == 2:
                                equal.update_params(hpf_fc=val)
                            elif state[2] == 3:
                                equal.update_params(hpf_N=val)
                            elif state[2] == 4:
                                pass
                        # bll 1
                        elif state[1] == 3: 
                            if   state[2] == 1:
                                equal.update_params(bll1_en=val)
                            elif state[2] == 2:
                                equal.update_params(bll1_fgm=val)
                            elif state[2] == 3:
                                equal.update_params(bll1_bfac=val)
                            elif state[2] == 4:
                                equal.update_params(bll1_gdb=val)
                        # bll 2
                        elif state[1] == 4: 
                            if   state[2] == 1:
                                equal.update_params(bll2_en=val)
                            elif state[2] == 2:
                                equal.update_params(bll2_fgm=val)
                            elif state[2] == 3:
                                equal.update_params(bll2_bfac=val)
                            elif state[2] == 4:
                                equal.update_params(bll2_gdb=val)
                    elif state[0] == 4: 
                        if   state[1] == 1:
                            master_pre_gain = 10**(val/20)
                        elif state[1] == 2:
                            master_post_gain = 10**(val/20)
                    fxbox.process = True
            except AttributeError:
                pass
        
        def on_release(key):
            pass
        
        def callback(asdf, frame_count, time_info, status):
            if fxbox.process == True:
                in_data = wfi.readframes(cfg.buffer_size)
                x = np.frombuffer(in_data, dtype=np.int16)
                x = x.reshape(cfg.buffer_size, 2)
                audio_stream = (x/2**15)
                audio_stream = audio_stream * master_pre_gain
                audio_stream = comp.compress(audio_stream)
                audio_stream = equal.equalize(audio_stream)
                audio_stream = conv.convolve(audio_stream)
                audio_stream = limiter.compress(audio_stream)
                audio_stream = audio_stream * master_post_gain
                y = (audio_stream*2**15).astype(np.int16)
                out_data = y.tobytes()
                if(np.max(audio_stream)>1):
                    print("clipping!")
            else:
                out_data = nothing
            # out_data = in_data
            return (out_data, pyaudio.paContinue)
        
        stream = p.open(format=pyaudio.paInt16,
                        channels=cfg.channels,
                        rate=cfg.samplerate,
                        output_device_index = 17,
                        output=True,
                        frames_per_buffer=cfg.buffer_size,
                        stream_callback=callback)
        
        stream.start_stream()
        # while stream.is_active():
        with keyboard.Listener(
                on_press=on_press,
                on_release=on_release) as listener:
            listener.join()
        print("yo")
        time.sleep(1)
        pass
        
        stream.stop_stream()
        p.terminate()
    
if __name__ == "__main__":
    main()