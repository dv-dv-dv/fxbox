import cython
import numpy as np; cimport numpy as np; np.import_array()
# user imports
import config as cfg
# numpy type defs
ITYPE = np.int16  # int type
ctypedef np.int16_t ITYPE_t
FTYPE = np.double;   # float type
ctypedef np.double_t FTYPE_t
@cython.boundscheck(False) # turn off bounds-checking for entire function
@cython.wraparound(False)  # turn off negative index wrapping for entire function
@cython.cdivision(True)
cdef class Convolver:
    cdef short[:] filter_lengths, offsets
    cdef double[:] convolution_buffer
    cdef double complex[:] filter_fft
    cdef int[:] filter_indices_fft
    cdef int number_of_filters, longest_filter, count, count_max, buffer
    cdef short[:, ::1] previous_buffers
    cdef bint realtime
    cdef object convolution_queue
    # cdef object convolution_queue
    def __init__(self, impulse, realtime=False):
        self.buffer = cfg.buffer
        self.set_impulse(impulse)
        self.realtime=realtime
    
    # this function does the necessary work in order to get the impulse ready for use
    cdef set_impulse(self, impulse):
        # get impulse from wav file
        
        height = cfg.height
        n_cap = cfg.n_cap;
        (filter_lengths, longest_filter, filter_indices, offsets, convolution_buffer_length) = self.partition_filter((impulse.shape[0] + self.buffer - 1)//self.buffer, height, n_cap)
        (filter_fft, filter_indices_fft) = self.compute_filter_fft(impulse, filter_lengths, filter_indices)
        
        self.filter_lengths = filter_lengths
        self.offsets = offsets
        self.filter_fft = filter_fft
        self.filter_indices_fft = filter_indices_fft
        self.number_of_filters = filter_lengths.size
        self.longest_filter = longest_filter
        self.previous_buffers = np.zeros((longest_filter, self.buffer), dtype=np.int16)
        self.convolution_buffer = np.zeros(convolution_buffer_length*self.buffer, dtype=np.double)
        self.count = 0
        self.count_max = convolution_buffer_length
    
    cdef import_from_wave(self, wave_file):
        import wave
        wfi = wave.open(wave_file, 'rb')
        wave_bytes = wfi.readframes(wfi.getnframes())
        wfi.close()
        return np.frombuffer(wave_bytes, dtype=np.int16).reshape(-1,2)
    
    cdef partition_filter(self, filter_length, height, n_cap):
        space_left = -filter_length
        filter_lengths = np.zeros(filter_length, dtype=np.int16)
        filter_indices = np.zeros(filter_length, dtype=np.int32)
        offsets = np.zeros(filter_length, dtype=np.int16)
        
        i = 0 # index
        n = 0 # represents a power of 2 i.e. 2^n
        prev_filter_length = -1
        
        while space_left < 0:
            filter_lengths[i] = 2**n
            filter_indices[i + 1] = filter_lengths[i]*self.buffer + filter_indices[i] 
            space_left = space_left + filter_lengths[i]
            
            if filter_lengths[i]==prev_filter_length:
                offsets[i + 1] = offsets[i] + filter_lengths[i]
            else:
                offsets[i + 1] = offsets[i]
                
            prev_filter_length = filter_lengths[i]
            n = n + (i%height + 1)//height
            if n>n_cap: n=n_cap
            i = i + 1
    
        # truncate arrays
        filter_lengths = filter_lengths[0:i]
        filter_indices = filter_indices[0:i+1]  
        offsets = offsets[1:i+1]
        longest_filter = filter_lengths[filter_lengths.shape[0] - 1]
        convolution_buffer_length = ((np.sum(filter_lengths) + longest_filter - 1)//longest_filter)*longest_filter
        return filter_lengths, longest_filter, filter_indices, offsets, convolution_buffer_length
        
    cdef compute_filter_fft(self, impulse, filter_lengths, filter_indices):
        # add zeros so that the sum of partitioned impulses 
        # and the impulse are the same length
        space_left = np.sum(filter_lengths) - (impulse.shape[0] + self.buffer - 1)//self.buffer
                                                        
        zeros_to_add = (space_left + 1)*self.buffer - impulse.shape[0]%self.buffer
        impulse = np.append(impulse, np.zeros(zeros_to_add, dtype=np.int16))
        
        #compute fft of partitioned impulses
        filter_fft = np.zeros(impulse.shape[0] + filter_lengths.shape[0], dtype=np.cdouble)
        filter_indices_fft_test = filter_indices*2
        filter_indices_fft = np.zeros(filter_indices.shape[0], dtype=np.int32)
        for j in range(0, filter_lengths.shape[0]):
            n = 2*filter_lengths[j]*self.buffer
            part_of_impulse = impulse[filter_indices[j]:filter_indices[j+1]]
            part_of_filter_fft = np.fft.rfft(part_of_impulse, n)
            filter_indices_fft[j+1] = filter_indices_fft[j] + part_of_filter_fft.shape[0]
            filter_fft[filter_indices_fft[j]:filter_indices_fft[j+1]] = part_of_filter_fft
        return filter_fft, filter_indices_fft
    
    def convolve(self, short[:] audio_in):
        cdef short[:] audio_to_filter, audio_out
        cdef double complex[:] audio_to_filter_fft
        cdef int buffer_pos, i
        buffer_pos = self.count%self.longest_filter
        # save audio sample
        self.previous_buffers[buffer_pos, :] = audio_in
        for i in range(self.number_of_filters):
            if (self.count + 1)%self.filter_lengths[i] != 0: break
            elif (i==0)|(self.filter_lengths[i]!=self.filter_lengths[i-1]):
                audio_to_filter = self.get_n_previous_buffers(self.filter_lengths[i])
                audio_to_filter_fft = np.fft.rfft(audio_to_filter, 2*self.filter_lengths[i]*self.buffer)
            self.add_to_convolution_buffer(self.convolve_with_filter_fft(audio_to_filter_fft, i), self.offsets[i])
         
        audio_out = self.get_from_convolution_buffer()
        self.count = (self.count + 1)%self.count_max
        return audio_out
    
    cdef get_from_convolution_buffer(self):
        cdef int index1 = (self.count)*self.buffer
        cdef int index2 = (self.count + 1)*self.buffer
        cdef np.ndarray[np.double_t] audio_out = np.round(0.5*np.asarray(self.convolution_buffer[index1:index2])/2**15)
        self.convolution_buffer[index1:index2] = 0
        return audio_out.astype(np.int16)
    
    cdef add_to_convolution_buffer(self, double[:] audio_in, int offset):
        cdef int index1, index2, diff1, diff2
        # assigning to a typed memory view like array[index1:index2] is only possible 
        # if there is only one thing on the right side of the equals sign
        # i.e. array[index1:index2] = temp
        cdef double[:] temp 
        index1 = ((self.count + offset)%self.count_max)*self.buffer
        index2 = index1 + audio_in.shape[0]
        if index2 > self.convolution_buffer.shape[0]:
            diff1 = self.convolution_buffer.shape[0] - index1
            diff2 = audio_in.shape[0] - diff1
            temp = np.asarray(self.convolution_buffer[index1:index1 + diff1]) + np.asarray(audio_in[0:diff1])
            self.convolution_buffer[index1:index1 + diff1] = temp
            temp = np.asarray(self.convolution_buffer[0:diff2]) + np.asarray(audio_in[diff1:diff1 + diff2])
            self.convolution_buffer[0:diff2] = temp
        else:
            temp = np.asarray(self.convolution_buffer[index1:index2]) + np.asarray(audio_in)
            self.convolution_buffer[index1:index2] = temp
        
    cdef convolve_with_filter_fft(self, double complex[:] audio_to_filter_fft, int filter_index):
        cdef np.ndarray[np.cdouble_t] filter_fft = np.asarray(self.get_filter_fft(filter_index))
        cdef np.ndarray[np.cdouble_t] audio_out_fft = filter_fft*np.asarray(audio_to_filter_fft)
        cdef np.ndarray[np.double_t] audio_out = np.fft.irfft(audio_out_fft)
        return audio_out
    
    cdef get_n_previous_buffers(self, int n):
        cdef int count_pb = self.count%self.longest_filter
        cdef int index1 = count_pb + 1 - n
        cdef int index2 = count_pb + 1        
        cdef short[:, :] n_previous_samples
        if index1 < 0:
            index1 = index1 + self.previous_buffers.shape[0]
            diff1 = self.previous_buffers.shape[0] - index1
            diff2 = n - diff1
            n_previous_samples = np.zeros((n, self.buffer), dtype=np.int16)
            n_previous_samples[0:diff1, :] = self.previous_buffers[index1:index1 + diff1, :]
            n_previous_samples[diff1:diff1 + diff2, :] = self.previous_buffers[0:diff2, :]
        else:
            n_previous_samples = self.previous_buffers[index1:index2, :]
        n_previous_samples = np.asarray(n_previous_samples).reshape(-1,1)
        return n_previous_samples[:, 0]
    
    cdef get_filter_fft(self, int filter_index):
        cdef int index1, index2
        index1 = self.filter_indices_fft[filter_index]
        index2 = self.filter_indices_fft[filter_index + 1]
        return self.filter_fft[index1:index2]
    
class Convolver2():
    def __init__(self, impulse_file):
        impulse = self.import_from_wave(impulse_file)
        self.set_impulse(impulse)
        
    def set_impulse(self, impulse):
        self.channel1 = Convolver(impulse[:, 0])
        self.channel2 = Convolver(impulse[:, 1])

    def convolve(self, short[:, :] audio_in):
        cdef short[:] channel1_out, channel2_out
        cdef np.ndarray[ITYPE_t, ndim=2] audio_out
        channel1_out = self.channel1.convolve(audio_in[:, 0])
        channel2_out = self.channel2.convolve(audio_in[:, 1])
        audio_out = np.stack((channel1_out, channel2_out), axis=1)
        return audio_out
    
    def convolution_worker(self):
        self.channel1.convolution_worker()
        self.channel2.convolution_worker()
        
    def import_from_wave(self, wave_file):
        import wave
        wfi = wave.open(wave_file, 'rb')
        wave_bytes = wfi.readframes(wfi.getnframes())
        wfi.close()
        return np.frombuffer(wave_bytes, dtype=np.int16).reshape(-1, 2)