import numpy as np
import math
# user imports
import config as cfg

class Convolver:
    def __init__(self):
        self.set_impulse()
        self.count = 0
        pass
    
    def set_impulse(self):
        # get impulse from wav file
        import wave
        wfi = wave.open('IMPSpring04.wav', 'rb')
        impulse_bytes = wfi.readframes(wfi.getnframes())
        wfi.close()
        
        # put impulse into a useful format
        impulse = np.frombuffer(impulse_bytes, dtype=np.int16).reshape(-1,2)
        
        # partition impulse starting with h0
        first_filter_length = 7
        height = 2
        n_start = 0
        n_cap = 99
        (filter_lengths, filter_indices, offsets) = self.partition_impulse(math.ceil(impulse.shape[0]/cfg.buffer), first_filter_length, height, n_start, n_cap)
        (first_filter_fft, filter_fft, filter_indices_fft) = self.compute_filter_fft(impulse, first_filter_length, filter_lengths, filter_indices)
        self.filter_lengths = filter_lengths
        self.offsets = offsets
        self.first_filter_fft = first_filter_fft
        self.filter_fft = filter_fft
        self.filter_indices_fft = filter_indices_fft
        self.number_of_filters = filter_lengths.size
        self.previous_buffers = np.zeros((2560, cfg.buffer), dtype=np.int16)
        self.convolution_buffer = np.zeros((2*self.previous_buffers.size, 1), dtype=np.double)
        pass
    
    def partition_impulse(self, impulse_length, first_filter_length, height, n_start ,n_cap):
        space_left = -impulse_length + first_filter_length
        filter_lengths = np.zeros(impulse_length, dtype=np.int16)
        filter_indices = np.zeros(impulse_length, dtype=np.int32)
        offsets = np.zeros(impulse_length, dtype=np.int32)
        
        i = 0 # index
        n = n_start # nth power of 2
        prev_filter_length = -1
        
        while space_left < 0:
            filter_lengths[i] = 2**n
            filter_indices[i + 1] = (2**n)*cfg.buffer + filter_indices[i] 
            space_left = space_left + 2**n
            
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
        offsets = offsets[1:i+1] + first_filter_length
        return filter_lengths, filter_indices, offsets
        
    def compute_filter_fft(self, impulse, first_filter_length, filter_lengths, filter_indices):
        first_filter = impulse[0:first_filter_length*cfg.buffer, :]
        first_filter_fft = np.fft.fft(first_filter, (first_filter_length + 1)*cfg.buffer, axis=0)
        impulse = impulse[first_filter_length*cfg.buffer:impulse.shape[0], :]

        # add zeros so that the sum of partitioned impulses 
        # and the impulse are the same length
        space_left = np.sum(filter_lengths) - math.ceil(impulse.shape[0]/cfg.buffer)
                                                        
        zeros_to_add = (space_left + 1)*cfg.buffer - impulse.shape[0]%cfg.buffer
        impulse = np.append(impulse, np.zeros((zeros_to_add, impulse.shape[1]), dtype=np.int16)).reshape(-1, 2)
        
        #compute fft of partitioned impulses
        filter_fft = np.zeros((2*impulse.shape[0], impulse.shape[1]), dtype=np.cdouble)
        filter_indices_fft = filter_indices*2
        for j in range(0, filter_lengths.shape[0]):
            part_of_impulse = impulse[filter_indices[j]:filter_indices[j+1], :]
            part_of_filter_fft = np.fft.fft(part_of_impulse, 2*filter_lengths[j]*cfg.buffer, axis = 0)
            filter_fft[filter_indices_fft[j]:filter_indices_fft[j+1], :] = part_of_filter_fft
        
        return first_filter_fft[:,1], filter_fft[:, 1], filter_indices_fft
    
    def convolve(self, audio_in):
        #save to previous buffers
        self.previous_buffers[self.count, :] = audio_in
        
        # compute first filter response
        audio_to_filter = audio_in
        audio_to_filter_fft = np.fft.fft(audio_to_filter, self.first_filter_fft.shape[0])
        self.add_to_convolution_buffer(self.convolve_with_filter_fft(audio_to_filter_fft, -1), 0)
        prev_filter_length = -1
        
        # determine which other filter responses to compute
        for i in range(0, self.number_of_filters):
            if (self.count + 1)%self.filter_lengths[i] != 0: 
                break
            elif prev_filter_length != self.filter_lengths[i]:
                audio_to_filter = self.get_n_previous_samples(self.filter_lengths[i])
                audio_to_filter_fft = np.fft.fft(audio_to_filter, 2*self.filter_lengths[i]*cfg.buffer, axis=0)
            self.add_to_convolution_buffer(self.convolve_with_filter_fft(audio_to_filter_fft, i), self.offsets[i])
            
            prev_filter_length = self.filter_lengths[i]
        
        audio_out = self.get_from_convolution_buffer()
        self.count = self.count + 1
        return audio_out
    
    def get_from_convolution_buffer(self, n=0):
        index1 = (self.count - n)*cfg.buffer
        index2 = (self.count + 1 - n)*cfg.buffer
        audio_out = np.round(0.5*self.convolution_buffer[index1:index2]/2**15)
        print("getting ", index1/cfg.buffer, " to ", index2/cfg.buffer, " from convolution buffer")
        return audio_out.astype(np.int16)
    
    def add_to_convolution_buffer(self, audio_in, offset):
        print("adding audio of size ", audio_in.shape[0]/cfg.buffer/2, " in ", offset, " buffer lengths from now")
        index1 = (self.count + offset)*cfg.buffer
        index2 = (self.count + offset)*cfg.buffer + audio_in.shape[0]
        self.convolution_buffer[index1:index2, :] += audio_in.reshape(-1,1)
        
    def convolve_with_filter_fft(self, audio_to_filter_fft, filter_index):
        if filter_index==-1: 
            filter_fft = self.first_filter_fft
        else: 
            filter_fft = self.get_filter_fft(filter_index)
        audio_out_fft = filter_fft*audio_to_filter_fft
        audio_out = np.fft.ifft(audio_out_fft, axis=0)
        print("convolving audio of length ", audio_to_filter_fft.shape[0]/cfg.buffer/2, " with filter in index ", filter_index, " which has length ", filter_fft.shape[0]/cfg.buffer/2)
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