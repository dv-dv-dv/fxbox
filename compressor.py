import numpy as np
import math

# user imports
import settings as cfg

class AudioCompressor:
    def __init__(self, T=cfg.T, R=cfg.R, W=cfg.W, P=cfg.P, M=cfg.M, atk=cfg.atk, rel=cfg.rel):
        # define instance variables
        self.T = T
        self.R = R
        self.W = W
        self.P = self.decibels_to_linear(P)
        self.M = M
        self.atk = math.exp(-1/(atk*cfg.samplerate))
        self.rel = math.exp(-1/(rel*cfg.samplerate))
        self.level_detector_prev_out = 0
        self.k = (2**(cfg.bytes_per_channel*8))/2
        
        # define vectorized functions
        self.vdecibels_to_linear = np.vectorize(self.decibels_to_linear)
        self.vlinear_to_decibels = np.vectorize(self.linear_to_decibels)
        self.vgain_computer = np.vectorize(self.gain_computer)
        self.vlevel_detect = np.vectorize(self.level_detect)

    # accepts an numpy array that contains two channel audio data
    # the audio data is then run through an audio compressor
    # outputs an numpy array that contains two channel audio data
    def compressor(self, audio_input):
        channel_1 = self.P*audio_input[:,0]
        channel_2 = self.P*audio_input[:,1]
        level_abs = abs(channel_1 + channel_2)
        level_db = self.vlinear_to_decibels(level_abs)
        odb2 = self.vgain_computer(level_db)
        odb3 = level_db - odb2
        odb4 = self.vlevel_detect(odb3)
        gdb1 = self.M - odb4
        g = self.vdecibels_to_linear(gdb1)
        out1 = np.multiply(channel_1.astype(float),g)
        out2 = np.multiply(channel_2.astype(float),g)
        out = np.stack((out1,out2),axis=1)
        audio_output = out.astype('i2')
        return audio_output
    
    # accepts an audio_level, an value that represents an audio signal's loudness in either db or abs.
    # outputs
    def level_detect(self, audio_level):
        if audio_level > self.level_detector_prev_out:
            o = self.atk*self.level_detector_prev_out + (1 - self.atk)*audio_level
        else:
            o = self.rel*self.level_detector_prev_out + (1 - self.rel)*audio_level
        self.level_detector_prev_out = o
        return o
    
    # accepts an audio_level, an value that represents an audio signal's loudness in either db or abs.
    def gain_computer(self, audio_level):
        if 2*(audio_level - self.T) < -self.W:
            o = audio_level
        elif 2*abs(audio_level - self.T) <= self.W:
            o = audio_level + (1/self.R-1)*((audio_level - self.T + self.W/2)**2)/(2*self.W)
        elif 2*(audio_level - self.T) > self.W:
            o = self.T + (audio_level - self.T)/self.R
        return o
    
    # accepts a linear value and then converts it into db
    def linear_to_decibels(self, linear_value):
        if(linear_value==0):
            db_value = -999999.0
        else:
            linear_value_fl = float(linear_value)/self.k
            db_value = 20*math.log10(linear_value_fl)
        return db_value
    
    # accepts a db value and then converts it to linear
    def decibels_to_linear(self, db_value):
        linear_value = 10**(db_value/20)
        return linear_value