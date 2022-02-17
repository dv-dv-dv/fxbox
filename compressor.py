import numpy as np
import math

# user imports
import config as cfg

class Compressor:
    def __init__(self, threshold=cfg.threshold, ratio=cfg.ratio, knee_width=cfg.knee_width, pre_gain=cfg.pre_gain, post_gain=cfg.post_gain, attack=cfg.attack, release=cfg.release):
        # define instance variables
        db_to_log2_constant = math.log10(2) * 20
        self.threshold = threshold / db_to_log2_constant
        self.ratio = ratio
        self.knee_width = knee_width / db_to_log2_constant
        self.pre_gain = pre_gain / db_to_log2_constant
        self.post_gain = post_gain / db_to_log2_constant
        self.attack = math.exp(-1/(attack*cfg.samplerate))
        self.release = math.exp(-1/(release*cfg.samplerate))
        self.level_detector_prev_out = 0
        self.k = (2**(cfg.bytes_per_channel*8))/2
        self.compute_params()
        
        asdf = np.int16
        # define vectorized functions
        self.v_log_to_linear = np.vectorize(self.log_to_linear)
        self.v_linear_to_log = np.vectorize(self.linear_to_log)
        self.v_gain_computer = np.vectorize(self.gain_computer)
        self.v_level_detector = np.vectorize(self.level_detector)
    
    def compress(self, audio_in):
        gain_linear = self.calculate_gain(audio_in)
        audio_out = audio_in.astype(np.double)*gain_linear
        return audio_out.astype(np.int16)
    
    def calculate_gain(self, audio_in):
        level_db = self.v_linear_to_log(audio_in)
        gain_computer_out = self.v_gain_computer(level_db)
        odb3 = level_db - gain_computer_out
        odb4 = self.v_level_detector(odb3)
        gain_in_db = self.post_gain - odb4
        gain_linear = self.v_log_to_linear(gain_in_db)
        return gain_linear
    # accepts an audio_level, a value that represents an audio signal's loudness in either db or abs.
    # outputs
    def level_detector(self, audio_level):
        if audio_level > self.level_detector_prev_out:
            out = self.attack*(self.level_detector_prev_out - audio_level) + audio_level
        else:
            out = self.release*(self.level_detector_prev_out - audio_level) + audio_level
        self.level_detector_prev_out = out
        return out
    
    def compute_params(self):
        # gain computer parameters
        self.gc_param1 = self.threshold - self.knee_width/2
        self.gc_param2 = self.threshold + self.knee_width/2
        self.gc_param3 = (1/self.ratio - 1)/(2*self.knee_width)
        self.gc_param4 = self.threshold*(1-1/self.ratio)
        
        # linear to log params
        self.l2log_param1 = math.log2(self.k)
        
    # accepts an audio_level, a value that represents an audio signal's loudness in either db or abs.
    def gain_computer(self, audio_level):
        if audio_level < self.gc_param1:
            out = audio_level
        elif audio_level <= self.gc_param2:
            out = audio_level + self.gc_param3*(audio_level - self.gc_param1)**2
        elif audio_level > self.gc_param2:
            out = audio_level/self.ratio + self.gc_param4
        return out
    
    def linear_to_log(self, linear_value):
        if(linear_value==0):
            db_value = -999999999999.9
        else:
            db_value = math.log2(abs(linear_value)) - self.l2log_param1
        return db_value
    
    # accepts a db value and then converts it to linear
    def log_to_linear(self, db_value):
        linear_value = 2**(db_value)
        return linear_value
    
class Compressor2(Compressor):
    def compress(self, audio_in):
        audio_in_mono = audio_in[:,0] + audio_in[:,1]
        gain_linear = self.calculate_gain(audio_in_mono)
        audio_out = audio_in.astype(np.double)
        audio_out[:, 0] *= gain_linear
        audio_out[:, 1] *= gain_linear
        return audio_out.astype(np.int16)