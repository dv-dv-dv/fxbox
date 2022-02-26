import numpy as np; cimport numpy as np; np.import_array()
import math
# user imports
import config as cfg

class Convolver:
    def __init__(self, impulse, realtime=False):
        self.set_impulse(impulse)
        self.realtime=realtime
    
    # this function does the necessary work in order to get the impulse ready for use
    def set_impulse(self, impulse):
        filter_length = math.ceil(impulse.shape[0]/cfg.buffer)
        n_step = cfg.n_step
        height = 2**n_step
        n_cap = math.log2(cfg.filter_size_cap/cfg.buffer)
        n_step = cfg.n_step
        (blocks_needed, filter_indices, offsets, convolution_buffer_length) = self.partition_filter(filter_length, height, n_cap, n_step)
        (filter_fft, filter_indices_fft) = self.compute_filter_fft(impulse, blocks_needed, filter_indices)
        
        self.blocks_needed = blocks_needed
        self.filter_lengths = blocks_needed.astype(np.int32)*cfg.buffer*2
        self.number_of_filters = blocks_needed.shape[0]
        self.offsets = offsets
        self.filter_fft = filter_fft
        self.filter_indices_fft = filter_indices_fft
        self.previous_buffers = np.zeros((blocks_needed[-1], cfg.buffer), dtype=np.int16)
        self.convolution_buffer = np.zeros(convolution_buffer_length*cfg.buffer, dtype=np.double)
        self.cq_split = height*((self.number_of_filters - height)//(height * 2))
        self.count = 0
        self.count_max = convolution_buffer_length
        
        
        self.filter_use  = np.zeros(blocks_needed.shape[0])
        self.no_rfft = 0
        self.no_irfft = 0
    
    def partition_filter(self, filter_length, height, n_cap, n_step):
        if height < 2**n_step - 1:
            height = 2**n_step - 1
        space_left = -filter_length
        blocks_needed = np.zeros(filter_length, dtype=np.int16)
        filter_indices = np.zeros(filter_length, dtype=np.int32)
        offsets = np.zeros(filter_length, dtype=np.int32)
        i = 0
        n = 0 # nth power of 2
        x = 0
        y = 0
        prev_filter_length = 0
        while space_left < 0:
            blocks_needed[i] = 2**n
            filter_indices[i + 1] = blocks_needed[i]*cfg.buffer + filter_indices[i] 
            space_left = space_left + blocks_needed[i]
            
            y = y + prev_filter_length
            if blocks_needed[i]!=prev_filter_length:
                x = x + blocks_needed[i] - prev_filter_length
            offsets[i] = y - x + 1
            prev_filter_length = blocks_needed[i]
            n = n + n_step*math.floor((i%height + 1)/height)
            if n>n_cap: n=n_cap
            i = i + 1
        
        # truncate arrays
        blocks_needed = blocks_needed[0:i]
        filter_indices = filter_indices[0:i+1]
        offsets = offsets[0:i]
        convolution_buffer_length = math.ceil(np.sum(blocks_needed)/blocks_needed[-1])*blocks_needed[-1]
        return blocks_needed, filter_indices, offsets, convolution_buffer_length
    
    def compute_filter_fft(self, impulse, blocks_needed, filter_indices):
        # add zeros so that the sum of partitioned impulses 
        # and the impulse are the same length
        space_left = np.sum(blocks_needed) - math.ceil(impulse.shape[0]/cfg.buffer)
                                                        
        zeros_to_add = (space_left + 1)*cfg.buffer - impulse.shape[0]%cfg.buffer
        impulse = np.append(impulse, np.zeros(zeros_to_add, dtype=np.int16))
        
        #compute fft of partitioned impulses
        filter_fft = np.zeros(impulse.shape[0] + blocks_needed.shape[0], dtype=np.cdouble)
        filter_indices_fft = np.zeros(filter_indices.shape[0], dtype=np.int32)
        for j in range(0, blocks_needed.shape[0]):
            n = 2*blocks_needed[j]*cfg.buffer
            filter_indices_fft[j+1] = filter_indices_fft[j] + n//2 + 1
            part_of_impulse = impulse[filter_indices[j]:filter_indices[j+1]]
            part_of_filter_fft = np.fft.rfft(part_of_impulse, n)
            filter_fft[filter_indices_fft[j]:filter_indices_fft[j+1]] = part_of_filter_fft
        return filter_fft, filter_indices_fft
    
    def convolve(self, audio_in):
        # save audio sample
        cdef int i
        self.previous_buffers[self.count%self.blocks_needed[-1], :] = audio_in
        for i in range(0, self.number_of_filters):
            if (self.count + 1)%self.blocks_needed[i] != 0: break
            elif (i==0)|(self.blocks_needed[i]!=self.blocks_needed[i-1]):
                audio_to_filter = self.get_n_previous_buffers(self.blocks_needed[i])
                audio_to_filter_fft = np.fft.rfft(audio_to_filter, self.filter_lengths[i])
                self.no_rfft += 1
            self.filter_use[i] += 1
            self.add_to_convolution_buffer(self.convolve_with_filter_fft(audio_to_filter_fft, i), self.offsets[i])
        
        audio_out = self.get_from_convolution_buffer()
        self.count = (self.count + 1)%self.count_max
        return audio_out
    
    def get_from_convolution_buffer(self):
        index1 = (self.count)*cfg.buffer
        index2 = (self.count + 1)*cfg.buffer
        audio_out = 0.5*self.convolution_buffer[index1:index2]/2**15
        self.convolution_buffer[index1:index2] = 0
        return audio_out.astype(np.int16)
    
    def add_to_convolution_buffer(self, audio_in, offset):
        index1 = ((self.count + offset)%self.count_max)*cfg.buffer
        index2 = index1 + audio_in.shape[0]
        if index2 > self.convolution_buffer.shape[0]:
            diff1 = self.convolution_buffer.shape[0] - index1
            diff2 = audio_in.shape[0] - diff1
            self.convolution_buffer[index1:index1 + diff1] += audio_in[0:diff1]
            self.convolution_buffer[0:diff2] += audio_in[diff1:diff1 + diff2]
        else:
            self.convolution_buffer[index1:index2] += audio_in
        
    def convolve_with_filter_fft(self, audio_to_filter_fft, filter_index):
        filter_fft = self.get_filter_fft(filter_index)
        audio_out_fft = filter_fft*audio_to_filter_fft
        audio_out = np.fft.irfft(audio_out_fft)
        self.no_irfft += 1
        return audio_out.real
    
    def get_n_previous_buffers(self, n):
        count_pb = self.count%self.blocks_needed[-1]
        index1 = count_pb + 1 - n
        index2 = count_pb + 1        
        if index1 < 0:
            index1 = index1 + self.previous_buffers.shape[0]
            diff1 = self.previous_buffers.shape[0] - index1
            diff2 = n - diff1
            n_previous_samples = np.zeros((n, cfg.buffer), dtype=np.int16)
            n_previous_samples[0:diff1, :] = self.previous_buffers[index1:index1 + diff1, :]
            n_previous_samples[diff1:diff1 + diff2, :] = self.previous_buffers[0:diff2, :]
        else:
            n_previous_samples = self.previous_buffers[index1:index2, :]
        n_previous_samples.shape = (-1, 1)
        return n_previous_samples[:, 0]
    
    def get_filter_fft(self, filter_index):
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
        
    def convolve(self, audio_in):
        channel1_out = self.channel1.convolve(audio_in[:, 0])
        channel2_out = self.channel2.convolve(audio_in[:, 1])
        audio_out = np.stack((channel1_out, channel2_out), axis=1) 
        return audio_out
    
    def import_from_wave(self, wave_file):
        import wave
        wfi = wave.open(wave_file, 'rb')
        wave_bytes = wfi.readframes(wfi.getnframes())
        wfi.close()
        return np.frombuffer(wave_bytes, dtype=np.int16).reshape(-1, 2)
    
    def print_fft_usage(self):
        no_rfft = self.channel1.no_rfft + self.channel2.no_rfft
        no_irfft = self.channel1.no_irfft + self.channel2.no_irfft
        print("rfft count ", no_rfft,"\t irfft count ", no_irfft, " over 2 channels")