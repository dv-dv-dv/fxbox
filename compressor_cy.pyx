import numpy as np; cimport numpy as np; np.import_array()
cimport libc.math as cmath
import cython

# user imports
import config as cfg

ITYPE = np.int16  # int type
ctypedef np.int16_t ITYPE_t
FTYPE = np.double;   # float type
ctypedef np.double_t FTYPE_t
@cython.boundscheck(False) # turn off bounds-checking for entire function
@cython.wraparound(False)  # turn off negative index wrapping for entire function

cdef class Compressor:
    cdef double threshold, ratio, knee_width, pre_gain, post_gain, attack, release, level_detector_prev_out, k
    cdef double gc_param1, gc_param2, gc_param3, gc_param4, l2log_param1
    def __init__(self, threshold=cfg.threshold, ratio=cfg.ratio, knee_width=cfg.knee_width, pre_gain=cfg.pre_gain, post_gain=cfg.post_gain, attack=cfg.attack, release=cfg.release):
        # define instance variables
        cdef double db_to_log2_constant = cmath.log10(2)*20
        self.threshold = threshold / db_to_log2_constant
        self.ratio = ratio
        self.knee_width = knee_width / db_to_log2_constant
        self.pre_gain = pre_gain / db_to_log2_constant
        self.post_gain = post_gain / db_to_log2_constant
        self.attack =cmath.exp(-1/(attack*cfg.samplerate))
        self.release =cmath.exp(-1/(release*cfg.samplerate))
        self.level_detector_prev_out = 0
        self.k = (2**(cfg.bytes_per_channel*8))/2 # max value of a 16 bit signed integer
        
        self.gc_param1 = self.threshold - self.knee_width/2
        self.gc_param2 = self.threshold + self.knee_width/2
        self.gc_param3 = (1/self.ratio - 1)/(2*self.knee_width)
        self.gc_param4 = self.threshold*(1-1/self.ratio)
        self.l2log_param1 =cmath.log2(self.k)
        
    def compress(self, np.ndarray[FTYPE_t] audio_in):
        cdef np.ndarray[FTYPE_t] gain_linear = self.calculate_gain(audio_in)
        cdef np.ndarray[FTYPE_t] audio_out = audio_in.astype(np.double)*gain_linear
        return audio_out.astype(np.int16)
    
    cdef calculate_gain(self, np.ndarray[ITYPE_t] audio_in):
        cdef np.ndarray[FTYPE_t] level_db = self.linear_to_log(audio_in)
        cdef np.ndarray[FTYPE_t] gain_computer_out = self.gain_computer(level_db)
        cdef np.ndarray[FTYPE_t] odb3 = level_db - gain_computer_out
        cdef np.ndarray[FTYPE_t] odb4 = self.level_detector(odb3)
        cdef np.ndarray[FTYPE_t] gain_in_db = self.post_gain - odb4
        cdef np.ndarray[FTYPE_t] gain_linear = self.log_to_linear(gain_in_db)
        return gain_linear
    # accepts an audio_level, a value that represents an audio signal's loudness in either db or abs.
    # outputs
    cdef level_detector(self, np.ndarray[FTYPE_t] audio_level):
        cdef np.ndarray[FTYPE_t] output = np.zeros(audio_level.shape[0], dtype=FTYPE)
        cdef int audio_level_length = audio_level.shape[0]
        for i in range(audio_level_length):
            if audio_level[i] > self.level_detector_prev_out:
                output[i] = self.attack*(self.level_detector_prev_out - audio_level[i]) + audio_level[i]
            else:
                output[i] = self.release*(self.level_detector_prev_out - audio_level[i]) + audio_level[i]
            self.level_detector_prev_out = output[i]
        return output
        
    # accepts an audio_level, a value that represents an audio signal's loudness in either db or abs.
    cdef gain_computer(self, np.ndarray[FTYPE_t] audio_level):
        cdef np.ndarray[FTYPE_t] output = np.zeros(audio_level.shape[0], dtype=FTYPE)
        cdef int audio_level_length = audio_level.shape[0]
        for i in range(audio_level_length):
            if audio_level[i] < self.gc_param1:
                output[i] = audio_level[i]
            elif audio_level[i] <= self.gc_param2:
                output[i] = audio_level[i] + self.gc_param3*cmath.pow(audio_level[i] - self.gc_param1, 2)
            elif audio_level[i] > self.gc_param2:
                output[i] = audio_level[i]/self.ratio + self.gc_param4
        return output
    
    cdef linear_to_log(self, np.ndarray[ITYPE_t] linear_array):
        cdef int linear_array_length = linear_array.shape[0]
        cdef np.ndarray[FTYPE_t] db_array = np.zeros(linear_array.shape[0], dtype=FTYPE)
        for i in range(linear_array_length):
            if(linear_array[i]==0):
                db_array[i] = -999999999999.9
            else:
                db_array[i] =cmath.log2(abs(linear_array[i])) - self.l2log_param1
            asdf = 2
        return db_array
    
    # accepts a db value and then converts it to linear
    cdef log_to_linear(self, np.ndarray[FTYPE_t] db_array):        
        cdef int db_array_array_length = db_array.shape[0]
        cdef np.ndarray[FTYPE_t] linear_array = np.zeros([db_array.shape[0]], dtype=FTYPE)
        for i in range(db_array_array_length):
            linear_array[i] = cmath.pow(2, db_array[i])
        return linear_array
    
cdef class Compressor2(Compressor):
    def compress(self, np.ndarray[ITYPE_t, ndim=2] audio_in):
        cdef np.ndarray[ITYPE_t] audio_in_mono = audio_in[:,0] + audio_in[:,1]
        cdef np.ndarray[FTYPE_t] gain_linear = self.calculate_gain(audio_in_mono)
        cdef np.ndarray[FTYPE_t, ndim=2] audio_out = audio_in.astype(FTYPE)
        audio_out[:, 0] *= gain_linear
        audio_out[:, 1] *= gain_linear
        return audio_out.astype(ITYPE)