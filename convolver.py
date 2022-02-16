import numpy as np
import math
# user imports
import config as cfg


class Convolver:
    def __init__(self):
        self.set_impulse()
        pass
    
    # this function does the necessary work in order to get the impulse ready for use
    def set_impulse(self):
        # get impulse from wav file
        impulse = self.import_from_wave('IMPSpring04.wav')
        
        # partition impulse starting with h0
        height = cfg.height
        n_start = cfg.n_start
        n_cap = math.ceil(math.log2(impulse.shape[0])) - 2;
        (filter_lengths, filter_indices, offsets, convolution_buffer_length) = self.partition_filter(math.ceil(impulse.shape[0]/cfg.buffer), height, n_start, n_cap)
        (filter_fft, filter_indices_fft) = self.compute_filter_fft(impulse[:,1], filter_lengths, filter_indices)
        
        self.filter_lengths = filter_lengths
        self.offsets = offsets
        self.filter_fft = filter_fft
        self.filter_indices_fft = filter_indices_fft
        self.number_of_filters = filter_lengths.size
        self.previous_buffers = np.zeros((3000, cfg.buffer), dtype=np.int16)
        self.convolution_buffer = np.zeros((6000*cfg.buffer, 1), dtype=np.double)
        self.count = 0
        self.count_max = convolution_buffer_length
    
    def import_from_wave(self, wave_file):
        import wave
        wfi = wave.open(wave_file, 'rb')
        wave_bytes = wfi.readframes(wfi.getnframes())
        wfi.close()
        return np.frombuffer(wave_bytes, dtype=np.int16).reshape(-1,2)
    
    def partition_filter(self, filter_length, height, n_start, n_cap):
        space_left = -filter_length
        filter_lengths = np.zeros(filter_length, dtype=np.int16)
        filter_indices = np.zeros(filter_length, dtype=np.int32)
        offsets = np.zeros(filter_length, dtype=np.int32)
        
        i = 0 # index
        n = n_start # represents a power of 2 i.e. 2^n
        prev_filter_length = -1
        
        while space_left < 0:
            filter_lengths[i] = 2**n
            filter_indices[i + 1] = filter_lengths[i]*cfg.buffer + filter_indices[i] 
            space_left = space_left + filter_lengths[i]
            
            if filter_lengths[i]==prev_filter_length:
                offsets[i + 1] = offsets[i] + filter_lengths[i]
            else:
                offsets[i + 1] = offsets[i]
                
            prev_filter_length = filter_lengths[i]
            n = n + math.floor((i%height + 1)/height)
            if n>n_cap: n=n_cap
            i = i + 1
    
        # truncate arrays
        filter_lengths = filter_lengths[0:i]
        filter_indices = filter_indices[0:i+1]
        offsets = offsets[1:i+1]
        convolution_buffer_length = math.ceil(np.sum(filter_lengths)/filter_lengths[-1])*filter_lengths[-1]
        return filter_lengths, filter_indices, offsets, convolution_buffer_length
        
    def compute_filter_fft(self, impulse, filter_lengths, filter_indices):
        # add zeros so that the sum of partitioned impulses 
        # and the impulse are the same length
        space_left = np.sum(filter_lengths) - math.ceil(impulse.shape[0]/cfg.buffer)
                                                        
        zeros_to_add = (space_left + 1)*cfg.buffer - impulse.shape[0]%cfg.buffer
        impulse = np.append(impulse, np.zeros(zeros_to_add, dtype=np.int16)).reshape(-1, 1)
        
        #compute fft of partitioned impulses
        filter_fft = np.zeros((impulse.shape[0] + filter_lengths.shape[0], impulse.shape[1]), dtype=np.cdouble)
        filter_indices_fft_test = filter_indices*2
        filter_indices_fft = np.zeros(filter_indices.shape[0], dtype=np.int32)
        for j in range(0, filter_lengths.shape[0]):
            n = 2*filter_lengths[j]*cfg.buffer
            filter_indices_fft[j+1] = filter_indices_fft[j] + n//2 + 1
            part_of_impulse = impulse[filter_indices[j]:filter_indices[j+1], :]
            part_of_filter_fft = np.fft.rfft(part_of_impulse, n, axis = 0)
            filter_fft[filter_indices_fft[j]:filter_indices_fft[j+1], :] = part_of_filter_fft
        return filter_fft.reshape(-1, 1), filter_indices_fft
    
    def convolve(self, audio_in):
        #save to previous buffers
        self.previous_buffers[self.count, :] = audio_in
        
        # compute first filter response
        
        # determine which other filter responses to compute
        for i in range(0, self.number_of_filters):
            if (self.count + 1)%self.filter_lengths[i] != 0: 
                break
            self.convolve_and_add_to_conv_buffer(i)
        
        audio_out = self.get_from_convolution_buffer()
        self.count = self.count + 1
        return audio_out
    
    def convolve_and_add_to_conv_buffer(self, filter_index):
        i = filter_index
        if i==0:
            audio_to_filter = self.get_n_previous_samples(self.filter_lengths[i])
            self.audio_to_filter_fft = np.fft.rfft(audio_to_filter, 2*self.filter_lengths[i]*cfg.buffer, axis=0)
        elif self.filter_lengths[i]!=self.filter_lengths[i-1]:
            audio_to_filter = self.get_n_previous_samples(self.filter_lengths[i])
            self.audio_to_filter_fft = np.fft.rfft(audio_to_filter, 2*self.filter_lengths[i]*cfg.buffer, axis=0)
        self.add_to_convolution_buffer(self.convolve_with_filter_fft(self.audio_to_filter_fft, i), self.offsets[i])
        pass
    
    def get_from_convolution_buffer(self, n=0):
        index1 = (self.count - n)*cfg.buffer
        index2 = (self.count + 1 - n)*cfg.buffer
        audio_out = np.round(0.5*self.convolution_buffer[index1:index2]/2**15)
        return audio_out.astype(np.int16)
    
    def add_to_convolution_buffer(self, audio_in, offset):
        index1 = (self.count + offset)*cfg.buffer
        index2 = (self.count + offset)*cfg.buffer + audio_in.shape[0]
        self.convolution_buffer[index1:index2, :] += audio_in.reshape(-1,1)
        
    def convolve_with_filter_fft(self, audio_to_filter_fft, filter_index):
        if filter_index==-1: 
            filter_fft = self.first_filter_fft
        else: 
            filter_fft = self.get_filter_fft(filter_index)
        audio_out_fft = filter_fft*audio_to_filter_fft
        audio_out = np.fft.irfft(audio_out_fft, axis=0)
        return audio_out.real
    
    def get_n_previous_samples(self, n):
        index1 = self.count + 1 - n
        index2 = self.count + 1
        n_previous_samples = self.previous_buffers[index1:index2, :]
        return n_previous_samples.reshape(-1, 1)
    
    def get_filter_fft(self, filter_index):
        index1 = self.filter_indices_fft[filter_index]
        index2 = self.filter_indices_fft[filter_index + 1]
        return self.filter_fft[index1:index2].reshape(-1,1)