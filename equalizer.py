from dataclasses import dataclass
import numpy as np
import scipy.signal as sps
import numba
import time

import config as cfg
import equalizer_cy
class Equalizer:
    # todo: implement Filter in cython
    @dataclass
    class Filter:
        a: np.ndarray
        b: np.ndarray
        a_flipped: np.ndarray
        b_flipped: np.ndarray
        y: np.ndarray
        x: np.ndarray
        nm_max: int
        
        def __init__(self, a: np.ndarray, b: np.ndarray):
            self.a = a
            self.b = b
            self.a_flipped = np.flip(a)
            self.b_flipped = np.flip(b)
            self.nm_max = max(a.shape[0], b.shape[0]) - 1
            self.x = np.zeros((cfg.buffer + self.nm_max, 2), np.double)
            self.y = np.zeros((cfg.buffer + self.nm_max, 2), np.double)
        
        def filter_audio(self, audio_in):
            audio_out, self.x, self.y = equalizer_cy.filter_audio(audio_in, self.a_flipped, self.b_flipped, self.nm_max, self.x, self.y)
            return audio_out
        
    def __init__(self):
        b_lpf, a_lpf = sps.butter(N=cfg.lowpass_order, Wn=cfg.lowpass_cutoff, fs=44100, btype='lowpass')
        self.lpf = self.Filter(a=a_lpf, b=b_lpf)
        b_hpf, a_hpf = sps.butter(N=cfg.highpass_order, Wn=cfg.highpass_cutoff, fs=44100, btype='highpass')
        self.hpf = self.Filter(a=a_hpf, b=b_hpf)
        self.bpf_cutoff = np.array(cfg.peaking_cutoff)
        self.bpf = np.empty(len(cfg.peaking_cutoff), dtype=object)
        # for i in range(len(cfg.peaking_cutoff)):
        #     b_bpf, a_bpf = sps.butter(N=cfg.peaking_order[i]*2, Wn=cfg.peaking_cutoff[i], fs=44100, btype='bandpass')
        #     self.bpf[i] = 0
            
        self.lpf_enabled = cfg.lowpass_enabled
        self.hpf_enabled = cfg.highpass_enabled
        
    def equalize(self, audio_in):
        if self.lpf_enabled==True:
            lpf_out = self.lpf.filter_audio(audio_in)
        else:
            lpf_out = audio_in
        if self.hpf_enabled==True:
            audio_out = self.hpf.filter_audio(lpf_out)
        else:
            audio_out = lpf_out
        return audio_out