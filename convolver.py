import numpy as np
import math
import multiprocessing as mp
import threading, queue
import time
# user imports
import config as cfg

def convolution_process(offsets, filter_indices_fft, filter_fft, filter_sizes, filter_sizes_fft, in_queue, out_queue):
    while True:
        irfft_time = 0
        (i, count, audio_to_filter_fft, list_of_is) = in_queue.get()
        is_length = list_of_is.shape[0]
        audio_out_fft_parallel = np.zeros((filter_sizes_fft[i], 2*is_length), dtype=np.cdouble)
        
        for n in range(is_length):
            index1 = filter_indices_fft[list_of_is[n]]
            index2 = filter_indices_fft[list_of_is[n] + 1]
            audio_out_fft_parallel[:, 2*n: 2*(n + 1)] =  filter_fft[index1:index2, :]*audio_to_filter_fft
        irfft_time -= time.perf_counter()
        audio_out_parallel = np.fft.irfft(audio_out_fft_parallel, axis=0)
        irfft_time += time.perf_counter()
        length = audio_out_parallel.shape[0]
        offsets_temp = offsets - offsets[list_of_is[0]]
        audio_out = np.zeros(((is_length + 1)*length//2, 2))
        
        for n in range(is_length):
            off = offsets_temp[list_of_is[n]]*cfg.buffer
            audio_out[off:off + length, :] += audio_out_parallel[:, 2*n:2*(n+1)]
        out_queue.put((offsets[list_of_is[0]], count, audio_out, irfft_time))
        in_queue.task_done()
        # (offset, count, audio_out, irfft_time)
class Convolver:
    def __init__(self, impulse_file, realtime=False):
        self.buffer = cfg.buffer
        self.parallel_max = cfg.parallel_max
        impulse = self.import_from_wave(impulse_file)
        self.channels = impulse.shape[1]
        self.set_impulse(impulse)
        self.realtime=realtime
        self.previous_buffers = np.zeros((self.buffer*self.blocks_needed[-1], self.channels), dtype=np.int16)
        self.convolution_buffer = np.zeros((self.convolution_buffer_length*self.buffer, self.channels), dtype=np.double)
        
        self.count = 0
        self.abs_count = 0
        self.no_rfft = 0
        self.no_irfft = 0
        self.rfft_timer = 0
        self.irfft_timer = 0
        self.convolution_queue = queue.PriorityQueue(-1)
        self.in_queue = mp.JoinableQueue(-1)
        self.out_queue = mp.JoinableQueue(-1)
        
        self.worker_process = threading.Thread(target=self.convolution_worker, daemon=True)
        self.worker_process.start()
        self.worker_process2 = threading.Thread(target=self.convolution_worker2, daemon=True)
        self.worker_process2.start()
        
        for _ in range(mp.cpu_count() - 1):
            mp.Process(target=convolution_process, args=(self.offsets, self.filter_indices_fft, self.filter_fft, self.filter_sizes, self.filter_sizes_fft, self.in_queue, self.out_queue)).start()

    def convolve(self, audio_in):
        # save audio sample
        bufferpos = self.buffer*(self.count%self.blocks_needed[-1])
        self.previous_buffers[bufferpos:bufferpos + self.buffer, :] = audio_in
        self.rfft_timer -= time.perf_counter()
        audio_to_filter_fft = np.fft.rfft(audio_in, (self.first_filter_length + 1)*self.buffer, axis=0)
        self.rfft_timer += time.perf_counter()
        self.no_rfft += 1
        self.irfft_timer -= time.perf_counter()
        audio_out = np.fft.irfft(audio_to_filter_fft*self.first_filter_fft, axis=0)
        self.irfft_timer += time.perf_counter()
        self.no_irfft += 1
        self.add_to_convolution_buffer(audio_out, 0, self.count)
        
        i = 0
        parallel = self.parallel_max
        while i < self.number_of_filters - 1:
            if (self.count + 1)%self.blocks_needed[i] != 0: break
            else:
                if(self.blocks_needed[i]==self.blocks_needed[-1]): parallel *= 100
                for j in range(i, self.number_of_filters):
                    if (self.blocks_needed[j] != self.blocks_needed[i])|(j==self.number_of_filters-1)|(j-i>=parallel):
                        list_of_is = np.arange(i, j)
                        break
                self.convolution_queue.put((self.abs_count + self.offsets[i], i, self.count, list_of_is))
            i = j
    
        if(self.realtime==False):
            self.convolution_queue.join()
            self.in_queue.join()
            self.out_queue.join()
        audio_out = self.get_from_convolution_buffer()
        self.abs_count += 1
        self.count = (self.abs_count)%self.convolution_buffer_length
        return audio_out

    def convolution_worker(self):
        from dataclasses import dataclass
        @dataclass
        class spectra:
            spectra: np.ndarray = np.zeros((1,1))
            count: int = -1
            blocks_needed: int = -1
            
        blocks_needed = self.blocks_needed
        block_sizes = self.block_sizes
        unique_blocks = np.unique(blocks_needed)
        filter_sizes = self.filter_sizes
        prev_filter = -1
        prev_count = -1
        vspectra = np.vectorize(spectra)
        spectras = vspectra(np.empty(unique_blocks.shape[0]))
        unique_spectras = unique_blocks.shape[0]
        offsets = self.offsets
        filter_indices_fft = self.filter_indices_fft
        filter_fft = self.filter_fft
        for i in range(unique_spectras):
            spectras[i].blocks_needed = unique_blocks[i]
            
        while True:
            spectra_needed = True
            (deadline, i, count, list_of_is) = self.convolution_queue.get()
            if (blocks_needed[i]!=prev_filter)|(count!=prev_count):
                for j in range(unique_spectras):
                    if spectras[j].blocks_needed==blocks_needed[i]:
                        index = j
                        if(spectras[j].count==count):
                            audio_to_filter_fft = spectras[j].spectra
                            spectra_needed = False
                        break
                if(spectra_needed==True):
                    audio_to_filter = self.get_n_previous_buffers(blocks_needed[i], count)
                    self.rfft_timer -= time.perf_counter()
                    audio_to_filter_fft = np.fft.rfft(audio_to_filter, filter_sizes[i], axis=0)
                    self.rfft_timer += time.perf_counter()
                    spectras[index].spectra = audio_to_filter_fft
                    spectras[index].count = count
                    self.no_rfft += 1
            prev_filter = blocks_needed[i]
            prev_count = count
            
            if(blocks_needed[i] > -1):
                is_length = list_of_is.shape[0]
                audio_out_fft_parallel = np.zeros((self.filter_sizes_fft[i], 2*is_length), dtype=np.cdouble)
                for n in range(is_length):
                    index1 = filter_indices_fft[list_of_is[n]]
                    index2 = filter_indices_fft[list_of_is[n] + 1]
                    audio_out_fft_parallel[:, 2*n: 2*(n + 1)] =  filter_fft[index1:index2, :]*audio_to_filter_fft
                self.irfft_timer -= time.perf_counter()
                audio_out_parallel = np.fft.irfft(audio_out_fft_parallel, axis=0)
                self.irfft_timer += time.perf_counter()
                self.no_irfft += 1
                for n in range(is_length):
                    self.add_to_convolution_buffer(audio_out_parallel[:, 2*n: 2*(n + 1)], offsets[list_of_is[n]], count)
            else:
                self.in_queue.put((i, count, audio_to_filter_fft, list_of_is))
            self.convolution_queue.task_done()
            
    def convolution_worker2(self):
        while True:
            (offset, count, audio_out, irfft_time) = self.out_queue.get()
            self.add_to_convolution_buffer(audio_out, offset, count)
            self.out_queue.task_done()
            self.no_irfft += 1
            self.irfft_timer += irfft_time
        
    def print_fft_usage(self):
        print("number of rfft:", self.no_rfft)
        print("number of irfft:", self.no_irfft)
        print("total number of rffts and irffts:", self.no_rfft + self.no_irfft)
        print("time spent doing rffts:", round(self.rfft_timer, 4))
        print("time spent doing irffts:", round(self.irfft_timer, 4))
        print("total time spent doing rffts and irffts:", round(self.rfft_timer + self.irfft_timer, 4))
        
    # this function does the necessary work in order to get the impulse ready for use
    def set_impulse(self, impulse):
        first_filter_length = 2**cfg.first_filter_power - 1
        first_filter_size = self.buffer*(2**cfg.first_filter_power - 1)
        first_filter = impulse[0:first_filter_size, :]
        self.first_filter_fft = np.fft.rfft(first_filter, first_filter_size + self.buffer, axis=0)
        self.first_filter_length = first_filter_length
        impulse = impulse[first_filter_size: impulse.shape[0] - 1, :]
        filter_length = math.ceil(impulse.shape[0]/self.buffer)
        n_step = cfg.n_step
        height = cfg.height
        n_cap = math.floor(math.log2(cfg.filter_size_cap/self.buffer))
        filter_indices = self.partition_filter(filter_length, height, n_cap, n_step)
        (impulse, filter_fft, filter_indices_fft) = self.compute_filter_fft(impulse, self.blocks_needed, filter_indices)
        self.filter_fft = filter_fft
        self.filter = impulse.astype(np.int32)
        self.filter_indices_fft = filter_indices_fft
        self.filter_indices = filter_indices

    def import_from_wave(self, wave_file, force_trim=cfg.force_trim):
        import os.path
        import wave
        wfi = wave.open(wave_file+".wav", 'rb')
        wave_bytes = wfi.readframes(wfi.getnframes())
        impulse = np.frombuffer(wave_bytes, dtype=np.int16)
        wfi.close()
        if(wfi.getnchannels()==1):
            impulse_temp = np.zeros((impulse.shape[0], 2), dtype=np.int16)
            impulse_temp[:, 0] = impulse_temp[:, 1] = impulse
            impulse = impulse_temp
        else:
            impulse = impulse.reshape(-1, 2)
        trim=False
        if((impulse.shape[0]>100000)&cfg.trim): 
            trim=True
            print("impulse is long, trimming...")
        if (trim==True) & (force_trim==False) & (os.path.exists(wave_file+"_trimmed.wav")):
            if(os.path.exists(wave_file+"_trimmed.wav")):
                wfi = wave.open(wave_file+"_trimmed.wav", 'rb')
                wave_bytes = wfi.readframes(wfi.getnframes())
                wfi.close()
                impulse = np.frombuffer(wave_bytes, dtype=np.int16).reshape(-1,2)
        elif(trim==True):
            if(trim ==True):
                window = 100
                impulse_abs = np.abs(impulse[:, 0]).astype(np.double) + np.abs(impulse[:, 1]).astype(np.double);
                intensity = np.zeros(impulse.shape[0] - window)
                
                for i in range(intensity.shape[0]):
                    intensity[i] = np.sqrt(np.sum(impulse_abs[i:i+window]**2))
                    
                trigger = np.max(intensity)/200
                
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
        filter_indices = np.zeros(filter_length + 1, dtype=np.int32)
        offsets = np.zeros(filter_length, dtype=np.int32)
        i = 0
        n = cfg.first_filter_power - 1 # nth power of 2
        x = 0
        y = 0
        prev_filter_length = 0
        while space_left < 0:
            blocks_needed[i] = 2**n
            filter_indices[i + 1] = blocks_needed[i]*self.buffer + filter_indices[i] 
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
        self.filter_sizes = self.blocks_needed.astype(np.int32)*self.buffer*2
        self.filter_sizes_fft = self.filter_sizes//2 + 1
        self.block_sizes = self.blocks_needed.astype(np.int32)*self.buffer
        self.offsets = offsets[0:i] + self.first_filter_length
        self.test = np.argsort(self.offsets)
        self.number_of_filters = self.blocks_needed.shape[0]
        self.convolution_buffer_length = math.ceil(np.sum(self.blocks_needed)/self.blocks_needed[-1])*self.blocks_needed[-1]
        print(self.blocks_needed)
        print(self.offsets)
        return filter_indices
    
    def compute_filter_fft(self, impulse, blocks_needed, filter_indices):
        # add zeros so that the sum of partitioned impulses 
        # and the impulse are the same length
        space_left = np.sum(blocks_needed) - math.ceil(impulse.shape[0]/self.buffer)
                                                        
        zeros_to_add = (space_left + 1)*self.buffer - impulse.shape[0]%self.buffer
        impulse = np.append(impulse, np.zeros((zeros_to_add, self.channels), dtype=np.int16)).reshape(-1, self.channels)
        
        #compute fft of partitioned impulses
        filter_fft = np.zeros((2*impulse.shape[0], self.channels), dtype=np.cdouble)
        filter_indices_fft = np.zeros(filter_indices.shape[0], dtype=np.int32)
        for j in range(0, blocks_needed.shape[0]):
            n = 2*blocks_needed[j]*self.buffer
            part_of_impulse = impulse[filter_indices[j]:filter_indices[j+1], :]
            part_of_filter_fft = np.fft.rfft(part_of_impulse, n, axis=0)
            filter_indices_fft[j+1] = filter_indices_fft[j] + part_of_filter_fft.shape[0]
            filter_fft[filter_indices_fft[j]:filter_indices_fft[j+1], :] = part_of_filter_fft
        return impulse, filter_fft[0:filter_indices_fft[-1]], filter_indices_fft
        
    def get_from_convolution_buffer(self):
        index1 = (self.count)*self.buffer
        index2 = (self.count + 1)*self.buffer
        audio_out = 0.5*self.convolution_buffer[index1:index2, :]/2**15
        self.convolution_buffer[index1:index2, :] = 0
        return audio_out.astype(np.int16)

    def add_to_convolution_buffer(self, audio_in, offset, count):
        index1 = ((count + offset)%self.convolution_buffer_length)*self.buffer
        index2 = index1 + audio_in.shape[0]
        if index2 > self.convolution_buffer.shape[0]:
            diff1 = self.convolution_buffer.shape[0] - index1
            diff2 = audio_in.shape[0] - diff1
            self.convolution_buffer[index1:index1 + diff1, :] += audio_in[0:diff1, :]
            self.convolution_buffer[0:diff2, :] += audio_in[diff1:diff1 + diff2, :]
        else:
            self.convolution_buffer[index1:index2, :] += audio_in

    def get_n_previous_buffers(self, n, count):
        count_pb = count%self.blocks_needed[-1]
        index1 = (count_pb + 1 - n)*self.buffer
        index2 = (count_pb + 1)*self.buffer
        if index1 < 0:
            index1 = index1 + self.previous_buffers.shape[0]
            diff1 = self.previous_buffers.shape[0] - index1
            diff2 = n - diff1
            n_previous_samples = np.zeros((n, self.buffer), dtype=np.int16)
            n_previous_samples[0:diff1, :] = self.previous_buffers[index1:index1 + diff1, :]
            n_previous_samples[diff1:diff1 + diff2, :] = self.previous_buffers[0:diff2, :]
        else:
            n_previous_samples = self.previous_buffers[index1:index2, :]
        return n_previous_samples
