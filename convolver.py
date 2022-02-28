import numpy as np
import math
from numpy import fft
import threading, queue
# user imports
import config as cfg

class Convolver:
    def __init__(self, impulse_file, realtime=False):
        impulse = self.import_from_wave(impulse_file)
        self.channels = impulse.shape[1]
        self.set_impulse(impulse)
        self.realtime=realtime
        self.previous_buffers = np.zeros((cfg.buffer*self.blocks_needed[-1], self.channels), dtype=np.int16)
        self.convolution_buffer = np.zeros((self.convolution_buffer_length*cfg.buffer, self.channels), dtype=np.double)
        self.count = 0
        self.filter_use  = np.zeros(self.blocks_needed.shape[0])
        self.no_rfft = 0
        self.no_irfft = 0
        self.convolution_queue = queue.PriorityQueue()
        if(realtime==False):
            threading.Thread(target=self.convolution_worker, daemon=True).start()
        # import wisdom_tools
        # pyfftw.import_wisdom(wisdom_tools.get_wisdom())
    
    # this function does the necessary work in order to get the impulse ready for use
    def set_impulse(self, impulse):
        filter_length = math.ceil(impulse.shape[0]/cfg.buffer)
        n_step = cfg.n_step
        height = 2**n_step
        n_cap = math.floor(math.log2(cfg.filter_size_cap/cfg.buffer))
        if(2**n_cap > filter_length/4): n_cap = math.floor(math.log2(filter_length/4))
        filter_indices = self.partition_filter(filter_length, height, n_cap, n_step)
        (impulse, filter_fft, filter_indices_fft) = self.compute_filter_fft(impulse, self.blocks_needed, filter_indices)
        self.filter_fft = filter_fft
        self.filter = impulse.astype(np.int32)
        self.filter_indices_fft = filter_indices_fft
        self.filter_indices = filter_indices

    def import_from_wave(self, wave_file, trim=False, force_trim=False):
        import os.path
        import wave
        if (trim==True) & (force_trim==False) & (os.path.exists(wave_file+"_trimmed.wav")):
            if(os.path.exists(wave_file+"_trimmed.wav")):
                wfi = wave.open(wave_file+"_trimmed.wav", 'rb')
                wave_bytes = wfi.readframes(wfi.getnframes())
                wfi.close()
                impulse = np.frombuffer(wave_bytes, dtype=np.int16).reshape(-1,2)
        else:
            import wave
            wfi = wave.open(wave_file+".wav", 'rb')
            wave_bytes = wfi.readframes(wfi.getnframes())
            wfi.close()
            impulse = np.frombuffer(wave_bytes, dtype=np.int16).reshape(-1,2)
            if(trim ==True):
                window = 100
                impulse_abs = np.abs(impulse[:, 0]).astype(np.double) + np.abs(impulse[:, 1]).astype(np.double);
                intensity = np.zeros(impulse.shape[0] - window)
                
                for i in range(intensity.shape[0]):
                    intensity[i] = np.sqrt(np.sum(impulse_abs[i:i+window]**2))
                    
                trigger = np.max(intensity)/50
                
                for i in range(intensity.shape[0]):
                    k = intensity.shape[0] - i - 1
                    if intensity[k] > trigger:
                        cutoff_point = k+window
                        print(cutoff_point)
                        break
                impulse = impulse[0:cutoff_point, :]
                import wave
                wfo = wave.open(wave_file+"_trimmed.wav", 'wb')
                wfo.setnchannels(2)
                wfo.setsampwidth(2)
                wfo.setframerate(44100)
                wfo.writeframes(impulse.tobytes())
        return impulse
    
    def partition_filter(self, filter_length, height, n_cap, n_step):
        if height < 2**n_step - 1:
            height = 2**n_step - 1
        space_left = -filter_length
        blocks_needed = np.zeros(filter_length, dtype=np.int16)
        filter_indices = np.zeros(filter_length, dtype=np.int32)
        offsets = np.zeros(filter_length, dtype=np.int32)
        i = 0
        n = cfg.delay_amount # nth power of 2
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
        
        filter_indices = filter_indices[0:i+1]
        self.blocks_needed = blocks_needed[0:i]
        self.filter_sizes = self.blocks_needed.astype(np.int32)*cfg.buffer*2
        self.block_sizes = self.blocks_needed.astype(np.int32)*cfg.buffer
        self.offsets = offsets[0:i] + 2**cfg.delay_amount-1
        self.number_of_filters = self.blocks_needed.shape[0]
        self.convolution_buffer_length = math.ceil(np.sum(self.blocks_needed)/self.blocks_needed[-1])*self.blocks_needed[-1]
        return filter_indices
    
    def compute_filter_fft(self, impulse, blocks_needed, filter_indices):
        # add zeros so that the sum of partitioned impulses 
        # and the impulse are the same length
        space_left = np.sum(blocks_needed) - math.ceil(impulse.shape[0]/cfg.buffer)
                                                        
        zeros_to_add = (space_left + 1)*cfg.buffer - impulse.shape[0]%cfg.buffer
        impulse = np.append(impulse, np.zeros((zeros_to_add, self.channels), dtype=np.int16)).reshape(-1, self.channels)
        
        #compute fft of partitioned impulses
        filter_fft = np.zeros((2*impulse.shape[0], self.channels), dtype=np.cdouble)
        filter_indices_fft = np.zeros(filter_indices.shape[0], dtype=np.int32)
        for j in range(0, blocks_needed.shape[0]):
            n = 2*blocks_needed[j]*cfg.buffer
            part_of_impulse = impulse[filter_indices[j]:filter_indices[j+1], :]
            part_of_filter_fft = fft.rfft(part_of_impulse, n, axis=0)
            filter_indices_fft[j+1] = filter_indices_fft[j] + part_of_filter_fft.shape[0]
            filter_fft[filter_indices_fft[j]:filter_indices_fft[j+1], :] = part_of_filter_fft
        return impulse, filter_fft[0:filter_indices_fft[-1]], filter_indices_fft
    
    def convolve(self, audio_in):
        # save audio sample
        bufferpos = cfg.buffer*(self.count%self.blocks_needed[-1])
        self.previous_buffers[bufferpos:bufferpos + cfg.buffer, :] = audio_in
        audio_to_filter = self.get_n_previous_buffers(self.blocks_needed[0], self.count)
        audio_to_filter_fft = fft.rfft(audio_to_filter, self.filter_sizes[0], axis=0)
        audio_out = self.convolve_with_filter_fft(audio_to_filter_fft, 0)
        self.add_to_convolution_buffer(audio_out, self.offsets[0], self.count)
        
        for i in range(1, self.number_of_filters):
            if (self.count + 1)%self.blocks_needed[i] != 0: break
            else:
                self.convolution_queue.put((i, self.count))
        if(self.realtime==False):
            self.convolution_queue.join()
        audio_out = self.get_from_convolution_buffer()
        self.count = (self.count + 1)%self.convolution_buffer_length
        return audio_out
    
    def convolution_worker(self):
        blocks_needed = self.blocks_needed
        filter_sizes = self.filter_sizes
        filter_indices_fft = self.filter_indices_fft
        offsets = self.offsets
        filter_fft = self.filter_fft
        while True:
            (i, count) = self.convolution_queue.get()
            if(i==1)|(blocks_needed[i]!=blocks_needed[i-1]):
                audio_to_filter = self.get_n_previous_buffers(blocks_needed[i], count)
                audio_to_filter_fft = fft.rfft(audio_to_filter, filter_sizes[i], axis=0)
                
            index1 = filter_indices_fft[i]
            index2 = filter_indices_fft[i + 1]
            filter_fft_part =  filter_fft[index1:index2, :]
            audio_out_fft = filter_fft_part*audio_to_filter_fft
            audio_out = fft.irfft(audio_out_fft, axis=0)
            audio_out = self.convolve_with_filter_fft(audio_to_filter_fft, i)
            self.add_to_convolution_buffer(audio_out, offsets[i], count)
            self.convolution_queue.task_done()
            
    def get_from_convolution_buffer(self):
        index1 = (self.count)*cfg.buffer
        index2 = (self.count + 1)*cfg.buffer
        audio_out = 0.5*self.convolution_buffer[index1:index2, :]/2**15
        self.convolution_buffer[index1:index2, :] = 0
        return audio_out.astype(np.int16)

    def add_to_convolution_buffer(self, audio_in, offset, count):
        index1 = ((count + offset)%self.convolution_buffer_length)*cfg.buffer
        index2 = index1 + audio_in.shape[0]
        if index2 > self.convolution_buffer.shape[0]:
            diff1 = self.convolution_buffer.shape[0] - index1
            diff2 = audio_in.shape[0] - diff1
            self.convolution_buffer[index1:index1 + diff1, :] += audio_in[0:diff1, :]
            self.convolution_buffer[0:diff2, :] += audio_in[diff1:diff1 + diff2, :]
        else:
            self.convolution_buffer[index1:index2, :] += audio_in

    def convolve_with_filter_fft(self, audio_to_filter_fft, filter_index):
        filter_fft = self.get_filter_fft(filter_index)
        audio_out_fft = filter_fft*audio_to_filter_fft
        audio_out = fft.irfft(audio_out_fft, axis=0)
        self.no_irfft += 1
        return audio_out

    def get_n_previous_buffers(self, n, count):
        count_pb = count%self.blocks_needed[-1]
        index1 = (count_pb + 1 - n)*cfg.buffer
        index2 = (count_pb + 1)*cfg.buffer
        if index1 < 0:
            index1 = index1 + self.previous_buffers.shape[0]
            diff1 = self.previous_buffers.shape[0] - index1
            diff2 = n - diff1
            n_previous_samples = np.zeros((n, cfg.buffer), dtype=np.int16)
            n_previous_samples[0:diff1, :] = self.previous_buffers[index1:index1 + diff1, :]
            n_previous_samples[diff1:diff1 + diff2, :] = self.previous_buffers[0:diff2, :]
        else:
            n_previous_samples = self.previous_buffers[index1:index2, :]
        return n_previous_samples

    def get_filter_fft(self, filter_index):
        index1 = self.filter_indices_fft[filter_index]
        index2 = self.filter_indices_fft[filter_index + 1]
        return self.filter_fft[index1:index2, :]
    
    def get_filter(self, filter_index):
        index1 = self.filter_indices[filter_index]
        index2 = self.filter_indices[filter_index + 1]
        return self.filter[index1:index2, :]
