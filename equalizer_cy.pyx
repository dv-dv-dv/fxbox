import numpy as np; cimport numpy as np; np.import_array()
import cython

ITYPE = np.int16  # int type
ctypedef np.int16_t ITYPE_t
FTYPE = np.double;   # float type
ctypedef np.double_t FTYPE_t
@cython.boundscheck(False) # turn off bounds-checking for entire function
@cython.wraparound(False)  # turn off negative index wrapping for entire function

def filter_audio(np.ndarray[ITYPE_t, ndim=2] audio_in, np.ndarray[FTYPE_t] a_flipped, np.ndarray[FTYPE_t] b_flipped, int nm_max, np.ndarray[FTYPE_t, ndim=2] x, np.ndarray[FTYPE_t, ndim=2] y):
    x[nm_max:x.shape[0], :] = audio_in
    y[nm_max:y.shape[0]] = 0.0 # all values in y must equal zero or a_flipped[nm_max] must equal 0
    cdef int i, n, j
    a_flipped[nm_max] = 0
    for i in range(audio_in.shape[0]):
        n = int(i + nm_max)
        for j in range(nm_max + 1):
            y[n, 0] += b_flipped[j]*x[i + j, 0] - a_flipped[j]*y[i + j, 0]
            y[n, 1] += b_flipped[j]*x[i + j, 1] - a_flipped[j]*y[i + j, 1]
    
    y[0:nm_max] = y[y.shape[0] - nm_max:y.shape[0]]
    x[0:nm_max] = x[x.shape[0] - nm_max:x.shape[0]]
    cdef np.ndarray[ITYPE_t, ndim=2] audio_out = y[nm_max:y.shape[0]].astype(np.int16)
    return audio_out, x, y