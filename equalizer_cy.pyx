import numpy as np; cimport numpy as np; np.import_array()
import cython

# user imports
import config as cfg

ITYPE = np.int16  # int type
ctypedef np.int16_t ITYPE_t
FTYPE = np.double;   # float type
ctypedef np.double_t FTYPE_t

@cython.boundscheck(False)
@cython.wraparound(False)
cdef class Equalizer:
    cdef double[:, :] x, y
    cdef double[:] b, a, b_flipped, a_flipped
    cdef int nm_max, buffer_size
    def __init__(self, b, a):
        self.a = a
        self.b = b
        self.a_flipped = np.flip(np.copy(a))
        self.a_flipped[self.nm_max] = 0
        self.b_flipped = np.flip(b)
        self.nm_max = max(a.shape[0], b.shape[0]) - 1
        self.x = np.zeros((cfg.buffer_size + self.nm_max, 2), np.double)
        self.y = np.zeros((cfg.buffer_size + self.nm_max, 2), np.double)
        self.buffer_size = cfg.buffer_size
        
    cpdef filter_audio(self, double[:, :] audio_in):
        self.x[self.nm_max:self.x.shape[0], :] = audio_in
        cdef int i, n, j, k
        for i in range(self.buffer_size):
            n = i + self.nm_max
            for j in range(self.nm_max + 1):
                k = i + j
                self.y[n, 0] += self.b_flipped[j]*self.x[k, 0] - self.a_flipped[j]*self.y[k, 0]
                self.y[n, 1] += self.b_flipped[j]*self.x[k, 1] - self.a_flipped[j]*self.y[k, 1]
        
        self.y[0:self.nm_max] = self.y[self.y.shape[0] - self.nm_max:self.y.shape[0]]
        self.x[0:self.nm_max] = self.x[self.x.shape[0] - self.nm_max:self.x.shape[0]]
        cdef double[:, :] audio_out = self.y[self.nm_max:self.y.shape[0]]
        return np.asarray(audio_out)