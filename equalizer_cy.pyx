import numpy as np; cimport numpy as np; np.import_array()
import cython

# user imports
import config as cfg
ITYPE = np.int16  # int type
ctypedef np.int16_t ITYPE_t
FTYPE = np.double;   # float type
ctypedef np.double_t FTYPE_t

cdef class Equalizer:
    cdef double[:, :] x, y
    cdef double[:] b, a, b_flipped, a_flipped
    cdef int nm_max
    def __init__(self, a, b):
        self.a = a
        self.b = b
        self.a_flipped = np.flip(a)
        self.a_flipped[self.nm_max] = 0
        self.b_flipped = np.flip(b)
        self.nm_max = max(a.shape[0], b.shape[0]) - 1
        self.x = np.zeros((cfg.buffer + self.nm_max, 2), np.double)
        self.y = np.zeros((cfg.buffer + self.nm_max, 2), np.double)
        
    cpdef filter_audio(self, double[:, :] audio_in):
        self.x[self.nm_max:self.x.shape[0], :] = audio_in
        self.y[self.nm_max:self.y.shape[0]] = 0.0 # all values in y must equal zero or a_flipped[nm_max] must equal 0
        cdef int i, n, j
        for i in range(audio_in.shape[0]):
            n = int(i + self.nm_max)
            for j in range(self.nm_max + 1):
                self.y[n, 0] += self.b_flipped[j]*self.x[i + j, 0] - self.a_flipped[j]*self.y[i + j, 0]
                self.y[n, 1] += self.b_flipped[j]*self.x[i + j, 1] - self.a_flipped[j]*self.y[i + j, 1]
        
        self.y[0:self.nm_max] = self.y[self.y.shape[0] - self.nm_max:self.y.shape[0]]
        self.x[0:self.nm_max] = self.x[self.x.shape[0] - self.nm_max:self.x.shape[0]]
        cdef double[:, :] audio_out = self.y[self.nm_max:self.y.shape[0]]
        return np.asarray(audio_out)