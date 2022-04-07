import numpy as np; cimport numpy as np; np.import_array()
cimport libc.math as cmath
import cython

# user imports
import config as cfg

ITYPE = np.int16  # int type
ctypedef np.int16_t ITYPE_t
FTYPE = np.double;   # float type
ctypedef np.double_t FTYPE_t

cdef class Compressor:
    cdef double threshold, ratio, knee_width, pre_gain, post_gain, attack, release, atk, rel, gcp1, gcp2, gcp3, gcp4, level_detector_prev_out
    cdef int buffer_size
    def __init__(self, threshold, ratio, knee_width, pre_gain, post_gain, attack, release):
        self.threshold = threshold
        self.ratio = ratio
        self.knee_width = (knee_width + 10**-5)
        self.pre_gain = pre_gain
        self.post_gain = post_gain
        self.attack = attack
        self.release = release
        self.level_detector_prev_out = 9
        self.gcp1 = self.threshold - self.knee_width/2
        self.gcp2 = self.threshold + self.knee_width/2
        self.gcp3 = (1/self.ratio - 1)/(2*self.knee_width)
        self.gcp4 = self.threshold*(1 - 1/self.ratio)
        self.atk = cmath.exp(-1/(self.attack*cfg.samplerate))
        self.rel = cmath.exp(-1/(self.release*cfg.samplerate))
    
    cpdef gain_computer(self, np.ndarray[FTYPE_t] audio_lvl_in):
        cdef np.ndarray[FTYPE_t] audio_lvl_out = np.zeros(cfg.buffer, dtype=np.double)
        cdef int i
        for i in range(cfg.buffer):
            if audio_lvl_in[i] < self.gcp1:
                audio_lvl_out[i] = audio_lvl_in[i]
            elif audio_lvl_in[i] <= self.gcp2:
                audio_lvl_out[i] = audio_lvl_in[i] + self.gcp3*cmath.pow((audio_lvl_in[i] - self.gcp1), 2)
            elif audio_lvl_in[i] > self.gcp2:
                audio_lvl_out[i] = audio_lvl_in[i]/self.ratio + self.gcp4
        return audio_lvl_out
 
    cpdef level_detector(self, np.ndarray[FTYPE_t] audio_lvl_in):
        cdef np.ndarray[FTYPE_t] audio_lvl_out = np.zeros(cfg.buffer, dtype=np.double)
        cdef double level_detector_prev_out
        cdef int i
        level_detector_prev_out = self.level_detector_prev_out
        for i in range(cfg.buffer):
            if audio_lvl_in[i] > level_detector_prev_out:
                audio_lvl_out[i] = self.atk*(level_detector_prev_out - audio_lvl_in[i]) + audio_lvl_in[i]
            else:
                audio_lvl_out[i] = self.rel*(level_detector_prev_out - audio_lvl_in[i]) + audio_lvl_in[i]
            level_detector_prev_out = audio_lvl_out[i]
        self.level_detector_prev_out = level_detector_prev_out
        return audio_lvl_out
    
    cpdef linear_to_log(self, np.ndarray[FTYPE_t] audio_level_in):
        cdef np.ndarray[FTYPE_t] audio_lvl_out = np.zeros(cfg.buffer, dtype=np.double)
        cdef int i
        for i in range(cfg.buffer):
            if(audio_level_in[i]==0):
                audio_lvl_out[i] = -99999
            else:
                audio_lvl_out[i] = 20*cmath.log10(abs(audio_level_in[i]))
        return audio_lvl_out
    
    cpdef log_to_linear(self, np.ndarray[FTYPE_t] audio_level_in):
        cdef np.ndarray[FTYPE_t] audio_lvl_out = np.zeros(cfg.buffer, dtype=np.double)
        for i in range(cfg.buffer):
            audio_lvl_out[i] = cmath.pow(10, audio_level_in[i]/20)
        return audio_lvl_out