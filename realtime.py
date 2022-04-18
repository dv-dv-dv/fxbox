def main():
    import pyaudio
    import time
    import numpy as np
    import threading
    from pynput import keyboard
    ##user imports
    import config as cfg
    import compressor
    import convolver
    import equalizer
    import fxboxsm
    
    p = pyaudio.PyAudio()
    
    print(p.get_default_host_api_info())
    no_indexes = p.get_device_count()
    
    for x in range(0, no_indexes):
         print(p.get_device_info_by_index(x))
         
    # fxbox = fxboxsm.FXBox()
    # comp = compressor.Compressor()
    # conv = convolver.Convolver()
    # equal = equalizer.Equalizer()
    
    # def on_press(key):
    #     try:
    #         state = fxbox.translator(key.char)
    #         fxbox.new_state(state)
    #     except AttributeError:
    #         pass
    
    # def on_release(key):
    #     pass
    
    
    # def callback(in_data, frame_count, time_info, status):
    #     x = np.frombuffer(in_data, dtype=np.int16)
    #     x = x.reshape(cfg.buffer_size, 2)
    #     audio_stream = x/2**15
    #     audio_stream = comp.compress(audio_stream)
    #     audio_stream = equal.equalize(audio_stream)
    #     audio_stream = conv.convolve(audio_stream)
    #     y = (audio_stream*2**15).astype(np.int16)
    #     out_data = y.tobytes()
    #     return (out_data, pyaudio.paContinue)
    
    # stream = p.open(format=pyaudio.paInt16,
    #                 channels=cfg.channels,
    #                 input_device_index = 2,
    #                 output_device_index = ,
    #                 rate=cfg.samplerate,
    #                 output=True,
    #                 input=True,
    #                 frames_per_buffer=cfg.buffer,
    #                 stream_callback=callback)
    
    # stream.start_stream()
    # while stream.is_active():
    #     with keyboard.Listener(
    #             on_press=on_press,
    #             on_release=on_release) as listener:
    #         listener.join()
    
    # stream.stop_stream()
    # p.terminate()
    
if __name__ == "__main__":
    main()