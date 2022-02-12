import numpy as np
import math
import wave
# user imports
import config as cfg

class Convolver:
    def __init__(self):
        self.wet = cfg.wet
        self.dry = cfg.dry
        self.post = cfg.post
        
        self.buffer_pos = 1
        
        ####
        self.n_max = 99
        self.height = 2
        self.first_impulse_length = 3
        self.set_impulse()
        
    def set_impulse(self):
        # get impulse from wave file
        f_impulse = wave.open('IMPSpring04.wav', 'rb')
        no_frames = f_impulse.getnframes()
        impulse_bytes = f_impulse.readframes(no_frames)
        impulse = np.frombuffer(impulse_bytes, dtype=np.int16)
        impulse.shape = (-1, 2)
        self.impulse_fft = self.partition_impulse(impulse)
        pass
    
    def partition_impulse(self, impulse):
        first_impulse = impulse[0:self.first_impulse_length*cfg.buffer + 1, 1]
        first_impulse_fft = np.fft.fft(first_impulse, (self.first_impulse_length + 1)*(cfg.buffer), axis=0)
        impulse = impulse[self.first_impulse_length*cfg.buffer:impulse.shape[0], :]
        # determine how to partition impulse
        space_left = -math.ceil(impulse.shape[0]/cfg.buffer)# count of how many buffer chunks need to be padded to the impulse
        imp_lengths = np.zeros(100, dtype=np.int16) # the length of a single partition measured in buffers
        imp_spaces = np.zeros(100, dtype=np.int32) # one partition of an impulse is imp_lengths[i] to imp_lengths[i+1] - 1
        imp_start = np.zeros(100, dtype=np.int32)
        imp_end = np.zeros(100, dtype=np.int32)
        n = 0 # nth power
        num_of_imps = 0
        
        while space_left < 0:
            space_left = space_left + 2**n
            imp_lengths[num_of_imps] = 2**n
            imp_spaces[num_of_imps + 1] = (2**(n))*cfg.buffer + imp_spaces[num_of_imps]
            imp_start[num_of_imps] = imp_spaces[num_of_imps]
            imp_end[num_of_imps] = imp_spaces[num_of_imps + 1] + 1
            n = n + math.floor((num_of_imps%self.height + 1)/self.height)
            num_of_imps = num_of_imps + 1
        
        # truncate the arrays
        imp_lengths = imp_lengths[0:num_of_imps]
        imp_spaces = imp_spaces[0:num_of_imps+1]
        imp_start = imp_start[0:num_of_imps]
        imp_end = imp_end[0:num_of_imps]
        
        zeros_to_add = (space_left + 1)*cfg.buffer - (impulse.shape[0])%cfg.buffer
        impulse = np.append(impulse, np.zeros((zeros_to_add, 2), dtype=np.int16)).reshape(-1,2)
        impulse_fft = np.zeros((impulse.shape[0]*2, 2), dtype=np.cdouble)
        
        # compute FFT of partioned impulses
        for i in range(0, num_of_imps):
            partition = impulse[imp_start[i]:imp_end[i], :]
            partition_fft = np.fft.fft(partition, 2*imp_lengths[i]*cfg.buffer, axis=0)
            impulse_fft[2*imp_spaces[i]:2*imp_spaces[i+1]] = partition_fft
        
        self.first_impulse_fft = first_impulse_fft
        self.imp_lengths = imp_lengths
        self.num_of_imps = num_of_imps
        self.impulse_fft_indexes = imp_spaces*2
        self.longest_imp = imp_lengths[-1]
        self.prev_buffers = np.zeros((imp_lengths[-1]*16, cfg.buffer), dtype=np.int16)
        self.conv_buffer = np.zeros((cfg.buffer*imp_lengths[-1]*16, 1), dtype=np.double)
        return impulse_fft[:,1]
        
    def convolve(self, audio_in):
        self.prev_buffers[self.buffer_pos, :] = audio_in
        audio_to_convolve_fft = np.fft.fft(audio_in, cfg.buffer*(1+self.first_impulse_length), axis=0)
        audio_convolved = self.fft_convolve(audio_to_convolve_fft, -1)
        self.add_to_conv_buffer(audio_convolved, 0)
        schedule = self.first_impulse_length
        for i in range(0, self.num_of_imps):
            if self.buffer_pos%self.imp_lengths[i]==0:
                # print("buffer position : \t", self.buffer_pos)
                # if(i>10):
                #     print("impulse length : \t", self.imp_lengths[i])
                audio_to_convolve = self.get_prev_buffers(self.imp_lengths[i])
                audio_to_convolve_fft = np.fft.fft(audio_to_convolve, 2*self.imp_lengths[i]*cfg.buffer, axis=0)
                audio_convolved = self.fft_convolve(audio_to_convolve_fft, i)
                self.add_to_conv_buffer(audio_convolved, schedule)
                schedule = schedule + self.imp_lengths[i]

                
        audio_out = np.round(self.conv_buffer[self.buffer_pos*cfg.buffer:(self.buffer_pos + 1)*cfg.buffer])
        audio_out = audio_out.astype('i2')
        self.buffer_pos = (self.buffer_pos + 1)%self.prev_buffers.shape[0]
        return audio_out
    
    def add_to_conv_buffer(self, audio_in, schedule):
        pos = cfg.buffer*(self.buffer_pos + schedule)
        if(pos < 641):
            print("y")
            print(audio_in.shape[0]/cfg.buffer/2)
        if audio_in.shape[0] > self.conv_buffer.shape[0] - pos:
            self.conv_buffer[pos:self.conv_buffer.size] = self.conv_buffer[pos:self.conv_buffer.size] + audio_in[0:self.conv_buffer.size-pos]
            self.conv_buffer[0:audio_in.shape[0] - (self.conv_buffer.size - pos)] = audio_in[self.conv_buffer.size-pos:audio_in.shape[0]]
            print("?>>>>?????????????????????????????????????????????????????")
        else:
            temp1 = self.conv_buffer[pos:pos + audio_in.shape[0]] + audio_in
            self.conv_buffer[pos:pos + audio_in.shape[0]] = temp1
        a = self.conv_buffer
        a = self.conv_buffer
            
    def get_prev_buffers(self, n):
        if n==1:
            audio_out = self.prev_buffers[self.buffer_pos, :]
        elif (index1 := self.buffer_pos - n + 1 )< 0:
            audio_out = np.zeros((n, cfg.buffer), dtype=np.int16)
            audio_out[0:-index1, :] = self.prev_buffers[self.prev_buffers.shape[0] + index1:self.prev_buffers.shape[0], :]
            audio_out[-index1:n, :] = self.prev_buffers[0:n+index1, :]
        else:
            audio_out = self.prev_buffers[self.buffer_pos -n + 1:self.buffer_pos + 1, :]
        audio_out = audio_out.reshape(-1, 1)
        return audio_out
    
    def fft_convolve(self, audio_in_fft, impulse_index):
        if impulse_index==-1:
            impulse_fft = self.first_impulse_fft
        else:
            impulse_fft = self.get_impulse(impulse_index)
        impulse_fft.shape = (-1, 1)
        audio_in_fft.shape = (-1, 1)
        audio_out_fft = audio_in_fft*impulse_fft
        audio_out = 0.5*np.fft.ifft(audio_out_fft, axis=0)/2**15
        audio_out = audio_out.real
        return audio_out
    
    # index is defined for 0 to num_of_imps - 1
    def get_impulse(self, impulse_index):
        impulse_index1 = self.impulse_fft_indexes[impulse_index]
        impulse_index2 = self.impulse_fft_indexes[impulse_index + 1]
        return self.impulse_fft[impulse_index1:impulse_index2]
