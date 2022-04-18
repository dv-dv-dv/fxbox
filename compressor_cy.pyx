import numpy as np; cimport numpy as np; np.import_array()
cimport libc.math as cmath
import cython

# user imports
import config as cfg

ITYPE = np.int16  # int type
ctypedef np.int16_t ITYPE_t
FTYPE = np.double;   # float type
ctypedef np.double_t FTYPE_t

@cython.boundscheck(False)
@cython.wraparound(False)
cdef class Compressor:
    cdef double threshold, ratio, knee_width, pre_gain, post_gain, attack, release, atk, hold, rel, gcp1, gcp2, gcp3, gcp4, ldpo
    cdef int buffer_size, hold_count, hold_counter
    cdef bint rms
    def __init__(self, threshold, ratio, knee_width, pre_gain, post_gain, attack, release, rms, hold, buffer_size=cfg.buffer_size):
        self.threshold = threshold
        self.ratio = ratio
        self.knee_width = (knee_width + 0.001)
        self.pre_gain = pre_gain
        self.post_gain = post_gain
        self.attack = attack
        self.release = release
        self.hold = hold
        self.rms = rms
        self.ldpo = -100.0
        self.buffer_size = buffer_size
        self.hold_counter = 0
        self.compute_params()
        
    cpdef compute_params(self):
        self.gcp1 = (1/self.ratio - 1)/(2*self.knee_width)
        self.gcp2 = -self.threshold + self.knee_width/2
        self.gcp3 = (1 - 1/self.ratio)*self.threshold
        self.gcp4 = 1/self.ratio
        self.atk = cmath.exp(-1/(self.attack*cfg.samplerate))
        self.rel = cmath.exp(-1/(self.release*cfg.samplerate))
        self.hold_count = int(self.hold*cfg.samplerate)
        
    cpdef np.ndarray[FTYPE_t] gain_computer(self, np.ndarray[FTYPE_t] audio_lvl_in):
        cdef np.ndarray[FTYPE_t] audio_lvl_out = np.zeros(self.buffer_size, dtype=np.double)
        cdef double test
        cdef int i
        for i in range(self.buffer_size):
            test = 2*(audio_lvl_in[i] - self.threshold)
            if test < -self.knee_width:
                audio_lvl_out[i] = audio_lvl_in[i]
            elif abs(test) <= self.knee_width:
                audio_lvl_out[i] = audio_lvl_in[i] + self.gcp1*cmath.pow((audio_lvl_in[i] + self.gcp2), 2)
            elif test > self.knee_width:
                audio_lvl_out[i] = self.gcp3 + audio_lvl_in[i]*self.gcp4
        return audio_lvl_out
    

    cpdef np.ndarray[FTYPE_t] level_detector(self, np.ndarray[FTYPE_t] audio_lvl_in):
        cdef np.ndarray[FTYPE_t] audio_lvl_out = np.zeros(self.buffer_size, dtype=np.double)
        cdef double ldpo, audio_lvl_in_i, audio_lvl_out_i
        cdef int i
        ldpo = self.ldpo
        for i in range(self.buffer_size):
            if self.rms == True: audio_lvl_in_i = audio_lvl_in[i]*audio_lvl_in[i]
            else: audio_lvl_in_i = audio_lvl_in[i]
            
            if audio_lvl_in_i > ldpo:
                audio_lvl_out_i = self.atk*ldpo + (1 - self.atk)*audio_lvl_in_i
            else:
                audio_lvl_out_i = self.rel*ldpo + (1 - self.rel)*audio_lvl_in_i
                
            if self.rms == True: audio_lvl_out[i] = cmath.sqrt(abs(audio_lvl_out_i))
            else: audio_lvl_out[i] = audio_lvl_out_i
            ldpo = audio_lvl_out_i
        self.ldpo = ldpo
        return audio_lvl_out
    
    cpdef np.ndarray[FTYPE_t] linear_to_log(self, np.ndarray[FTYPE_t] audio_level_in):
        cdef np.ndarray[FTYPE_t] audio_lvl_out = np.zeros(self.buffer_size, dtype=np.double)
        cdef int i
        for i in range(self.buffer_size):
            if audio_level_in[i]==0:
                audio_lvl_out[i] = -999
            else:
                audio_lvl_out[i] = 20*cmath.log10(abs(audio_level_in[i]))
        return audio_lvl_out
    
    cpdef np.ndarray[FTYPE_t] log_to_linear(self, np.ndarray[FTYPE_t] audio_level_in):
        cdef np.ndarray[FTYPE_t] audio_lvl_out = np.zeros(self.buffer_size, dtype=np.double)
        cdef int i
        for i in range(self.buffer_size):
            audio_lvl_out[i] = cmath.pow(10, audio_level_in[i]/20)
        return audio_lvl_out
