import numpy as np
import math

# user imports
import config as cfg
import compressor_cy

class Compressor:
    def __init__(self, threshold=cfg.threshold, ratio=cfg.ratio, knee_width=cfg.knee_width, pre_gain=cfg.pre_gain, post_gain=cfg.post_gain, attack=cfg.attack, release=cfg.release):
        db_to_log2_constant = math.log10(2)*20
        self.comp = compressor_cy.Compressor(threshold, ratio, knee_width, pre_gain, post_gain, attack, release)
        self.threshold = threshold 
        self.ratio = ratio
        self.knee_width = knee_width 
        self.pre_gain = pre_gain 
        self.post_gain = post_gain 
        self.attack = attack
        self.release = release
    
    def compress(self, audio_in):
        audio_in_mono = (audio_in[:, 0] + audio_in[:, 1])/2
        gain_linear = self.calculate_gain(audio_in_mono)
        audio_out = audio_in
        audio_out[:, 0] *= gain_linear
        audio_out[:, 1] *= gain_linear
        return audio_out
    
    def calculate_gain(self, audio_in):
        level_db = self.comp.linear_to_log(audio_in)
        gain_computer_out = self.comp.gain_computer(level_db)
        odb3 = level_db - gain_computer_out
        odb4 = self.comp.level_detector(odb3)
        gain_in_db = self.post_gain - odb4
        gain_linear = self.comp.log_to_linear(gain_in_db)
        return gain_linear