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
        self.first_filter_length = 3
        (self.first_filter_fft, self.filter_lengths, self.filter_fft, self.filter_indices_fft) = self.partition_impulse(impulse, self.first_filter_length, 1, 0, 999)
        self.previous_buffers = np.zeros((2560, cfg.buffer), dtype=np.int16)
        self.convolution_buffer = np.zeros((2*self.previous_buffers.size, 1), dtype=np.double)
        self.number_of_filters = self.filter_lengths.size
        self.filter_use_amount = np.zeros(self.number_of_filters)
        pass
    
    def partition_impulse(self, impulse, first_filter_length, height, n_start ,n_cap):
        # get first impulse
        # first_filter = impulse[0:first_filter_length*cfg.buffer + 1, :]
        # first_filter_fft = np.fft.fft(first_filter, (first_filter_length + 1)*cfg.buffer, axis=0)
        # impulse = impulse[first_filter_length*cfg.buffer:impulse.shape[0], :]
        
        # partition the rest
        space_left = -math.ceil(impulse.shape[0]/cfg.buffer)
        filter_lengths = np.zeros(3000, dtype=np.int16)
        impulse_indices = np.zeros(3000, dtype=np.int32)
        i = 0 # index
        n = n_start # nth power of 2
        
        while space_left < 0:
            filter_lengths[i] = 2**n
            impulse_indices[i + 1] = (2**n)*cfg.buffer + impulse_indices[i] 
            space_left = space_left + 2**n
            
            n = n + math.floor((i%height + 1)/height)
            if n>n_cap: n=n_cap
            i = i + 1
    
        # truncate arrays
        filter_lengths = filter_lengths[0:i]
        impulse_indices = impulse_indices[0:i+1]
        
        # add zeros so that the sum of partitioned impulses 
        # and the impulse are the same length
        zeros_to_add = (space_left + 1)*cfg.buffer - impulse.shape[0]%cfg.buffer
        impulse = np.append(impulse, np.zeros((zeros_to_add, impulse.shape[1]), dtype=np.int16)).reshape(-1, 2)
        
        #compute fft of partitioned impulses
        filter_fft = np.zeros((2*impulse.shape[0], impulse.shape[1]), dtype=np.cdouble)
        filter_indices_fft = impulse_indices*2
        for j in range(0, i):
            part_of_impulse = impulse[impulse_indices[j]:impulse_indices[j+1], :]
            part_of_filter_fft = np.fft.fft(part_of_impulse, 2*filter_lengths[j]*cfg.buffer, axis = 0)
            filter_fft[filter_indices_fft[j]:filter_indices_fft[j+1], :] = part_of_filter_fft
        
        return 0, filter_lengths, filter_fft[:, 1], filter_indices_fft
    
    def convolve(self, audio_in):
        self.previous_buffers[self.count, :] = audio_in
        
        
        # # compute first filter response
        # audio_to_filter = audio_in
        # audio_to_filter_fft = np.fft.fft(audio_to_filter, self.first_filter_fft.shape[0])
        # prev_filter_length = 3
        # self.add_to_convolution_buffer(self.convolve_with_filter_fft(audio_to_filter_fft, -1), 0)
        
        prev_filter_length = -1
        schedule = 0
        
        # determine which other filter responses to compute
        for i in range(0, self.number_of_filters):
            if (self.count + 1)%self.filter_lengths[i] != 0: break
        
            ##################################################
            if(prev_filter_length != self.filter_lengths[i]):
                audio_to_filter = self.get_n_previous_samples(self.filter_lengths[i])
                audio_to_filter_fft = np.fft.fft(audio_to_filter, 2*self.filter_lengths[i]*cfg.buffer, axis=0)
                
            self.add_to_convolution_buffer(self.convolve_with_filter_fft(audio_to_filter_fft, i), schedule)
            schedule += self.filter_lengths[i]
            # donezo
            prev_filter_length = self.filter_lengths[i]
            # debug stuff
            self.filter_use_amount[i] = self.filter_use_amount[i] + 1
        
        audio_out = self.get_from_convolution_buffer()
        self.count = self.count + 1
        return audio_out
    
    def convolve_and_add_to_buffer(self, audio_to_filter_fft, filter_index, schedule):
        pass
    
    def get_from_convolution_buffer(self, n=0):
        index1 = (self.count - n)*cfg.buffer
        index2 = (self.count + 1 - n)*cfg.buffer
        audio_out = np.round(0.5*self.convolution_buffer[index1:index2]/2**15)
        print("getting ", index1/cfg.buffer, " to ", index2/cfg.buffer, " from convolution buffer")
        return audio_out.astype(np.int16)
    
    def add_to_convolution_buffer(self, audio_in, schedule):
        print("adding audio of size ", audio_in.shape[0]/cfg.buffer/2, " in ", schedule, " buffer lengths from now")
        index1 = self.count*cfg.buffer
        index2 = self.count*cfg.buffer + audio_in.shape[0]
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