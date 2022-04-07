import numpy as np
import scipy.signal as sps

import config as cfg
import equalizer_cy
class Equalizer:        
    def __init__(self):
        b_lpf, a_lpf = sps.butter(N=cfg.lowpass_order, Wn=cfg.lowpass_cutoff, fs=44100, btype='lowpass')
        self.lpf = equalizer_cy.Equalizer(a_lpf, b_lpf)
        b_hpf, a_hpf = sps.butter(N=cfg.highpass_order, Wn=cfg.highpass_cutoff, fs=44100, btype='highpass')
        self.hpf = equalizer_cy.Equalizer(a_hpf, b_hpf)
        self.bpf_cutoff = np.array(cfg.peaking_cutoff)
        self.bpf = np.empty(len(cfg.peaking_cutoff), dtype=object)
        # for i in range(len(cfg.peaking_cutoff)):
        #     b_bpf, a_bpf = sps.butter(N=cfg.peaking_order[i]*2, Wn=cfg.peaking_cutoff[i], fs=44100, btype='bandpass')
        #     self.bpf[i] = 0
            
        self.lpf_enabled = cfg.lowpass_enabled
        self.hpf_enabled = cfg.highpass_enabled
        
    def equalize(self, audio_in):
        if self.lpf_enabled==True:
            lpf_out = self.lpf.filter_audio(audio_in.astype(np.double))
        else:
            lpf_out = audio_in
        if self.hpf_enabled==True:
            audio_out = self.hpf.filter_audio(lpf_out)
        else:
            audio_out = lpf_out
        return audio_out