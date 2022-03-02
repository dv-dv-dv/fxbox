import numpy as np
import math
import threading, queue
import time
# user imports
import config as cfg

class Convolver:
    def __init__(self, impulse_file, realtime=False):
        print("initializing convoler...")
        self.buffer = cfg.buffer
        self.parallel_max = cfg.parallel_max
        impulse = self.import_from_wave(impulse_file)
        
        self.channels = impulse.shape[1]
        self.set_impulse(impulse)
        self.realtime=realtime
        self.count = 0
        self.abs_count = 0
        self.number_of_rffts = 0
        self.number_of_irffts = 0
        self.time_spent_doing_rffts = 0
        self.time_spent_doing_irffts = 0
        self.convolution_queue = queue.PriorityQueue(-1)
        self.worker_process = threading.Thread(target=self.convolution_worker, daemon=True)
        self.worker_process.start()
        
    def convolve(self, audio_in):
        # save audio sample
        bufferpos = self.buffer*(self.count%self.buffers_needed[-1])
        self.previous_buffers[bufferpos:bufferpos + self.buffer, :] = audio_in
        
        # convolve with first filter
        self.time_spent_doing_rffts -= time.perf_counter()
        audio_to_filter_fft = np.fft.rfft(audio_in, (self.first_filter_length + 1)*self.buffer, axis=0)
        self.time_spent_doing_rffts += time.perf_counter()
        self.number_of_rffts += 1
        self.time_spent_doing_irffts -= time.perf_counter()
        audio_out = np.fft.irfft(audio_to_filter_fft*self.first_filter_fft, axis=0)
        self.time_spent_doing_irffts += time.perf_counter()
        self.number_of_irffts += 1
        self.add_to_convolution_buffer(audio_out, 0, self.count)
        
        # determine which other convolutions to do
        i = 0
        parallel = self.parallel_max
        while i < self.number_of_filters - 1:
            if (self.count + 1)%self.buffers_needed[i] != 0: break
            else:
                if(self.buffers_needed[i]==self.buffers_needed[-1]): parallel = 4*self.parallel_max
                for j in range(i, self.number_of_filters):
                    if (self.buffers_needed[j] != self.buffers_needed[i])|(j==self.number_of_filters-1)|(j-i>=parallel):
                        list_of_is = np.arange(i, j)
                        break
                self.convolution_queue.put((self.abs_count + self.offsets[i], self.count, i, list_of_is)) # the inclusion of i in the queue is only for tiebreaking purposes
            i = j
    
        if(self.realtime==False):
            self.convolution_queue.join()
            
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
            buffers_needed: int = -1
            
        unique_blocks = np.unique(self.buffers_needed)
        unique_spectras = unique_blocks.shape[0]
        prev_buffers_needed = -1
        prev_count = -1
        vspectra = np.vectorize(spectra)
        spectras = vspectra(np.empty(unique_spectras))
        for i in range(unique_spectras):
            spectras[i].buffers_needed = unique_blocks[i]
            
        while True:
            spectra_needed = True
            (deadline, count, i, list_of_is) = self.convolution_queue.get()
            # determine if an rfft was previously calculated for this audio sample
            if (self.buffers_needed[i]!=prev_buffers_needed)|(count!=prev_count):
                for j in range(unique_spectras):
                    if spectras[j].buffers_needed==self.buffers_needed[i]:
                        index = j
                        if(spectras[j].count==count):
                            audio_to_filter_fft = spectras[j].spectra
                            spectra_needed = False
                        break
                    
                if(spectra_needed==True):
                    audio_to_filter = self.get_n_previous_buffers(self.buffers_needed[i], count)
                    self.time_spent_doing_rffts -= time.perf_counter()
                    audio_to_filter_fft = np.fft.rfft(audio_to_filter, self.transform_size[i], axis=0)
                    self.time_spent_doing_rffts += time.perf_counter()
                    spectras[index].spectra = audio_to_filter_fft
                    spectras[index].count = count
                    self.number_of_rffts += 1
                    
            prev_buffers_needed = self.buffers_needed[i]
            prev_count = count
            
            is_length = list_of_is.shape[0]
            audio_out_fft_parallel = np.zeros((self.rfft_size[i], 2*is_length), dtype=np.cdouble)
            for n in range(is_length):
                index1 = self.filter_indices_fft[list_of_is[n]]
                index2 = self.filter_indices_fft[list_of_is[n] + 1]
                audio_out_fft_parallel[:, 2*n: 2*(n + 1)] =  self.filter_fft[index1:index2, :]*audio_to_filter_fft
            self.time_spent_doing_irffts -= time.perf_counter()
            audio_out_parallel = np.fft.irfft(audio_out_fft_parallel, axis=0)
            self.time_spent_doing_irffts += time.perf_counter()
            self.number_of_irffts += 1
            for n in range(is_length):
                self.add_to_convolution_buffer(audio_out_parallel[:, 2*n: 2*(n + 1)], self.offsets[list_of_is[n]], count)
            self.convolution_queue.task_done()
        
    def print_fft_usage(self):
        print("number of rffts:", self.number_of_rffts)
        print("number of irffts:", self.number_of_irffts)
        print("total number of rffts and irffts:", self.number_of_rffts + self.number_of_irffts)
        print("time spent doing rffts:", round(self.time_spent_doing_rffts, 4))
        print("time spent doing irffts:", round(self.time_spent_doing_irffts, 4))
        print("total time spent doing rffts and irffts:", round(self.time_spent_doing_rffts + self.time_spent_doing_irffts, 4))
        
    # this function does the necessary work in order to get the impulse ready for use
    def set_impulse(self, impulse):
        # set first filter
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
        (impulse, filter_fft, filter_indices_fft) = self.compute_filter_fft(impulse, self.buffers_needed, filter_indices)
        self.filter_fft = filter_fft
        self.filter_indices_fft = filter_indices_fft
        self.previous_buffers = np.zeros((self.buffer*self.buffers_needed[-1], self.channels), dtype=np.int16)
        self.convolution_buffer = np.zeros((self.convolution_buffer_length*self.buffer, self.channels), dtype=np.double)

    def import_from_wave(self, wave_file, force_trim=cfg.force_trim):
        import os.path
        import wave
        wfi = wave.open(wave_file + ".wav", 'rb')
        wave_bytes = wfi.readframes(wfi.getnframes())
        impulse = np.frombuffer(wave_bytes, dtype=np.int16)
        wfi.close()
        if(wfi.getnchannels()==1):
            print("impulse is mono, copying to two channels")
            impulse_temp = np.zeros((impulse.shape[0], 2), dtype=np.int16)
            impulse_temp[:, 0] = impulse_temp[:, 1] = impulse
            impulse = impulse_temp
        else:
            impulse = impulse.reshape(-1, 2)
        trim=False
        if((impulse.shape[0]>100000)&cfg.trim): 
            trim=True
            print("impulse is long...")
        if (trim==True) & (force_trim==False) & (os.path.exists(wave_file+"_trimmed.wav")):
            print("trimmed version of impulse found, using that one instead")
            wfi = wave.open(wave_file+"_trimmed.wav", 'rb')
            wave_bytes = wfi.readframes(wfi.getnframes())
            wfi.close()
            impulse = np.frombuffer(wave_bytes, dtype=np.int16).reshape(-1,2)
        elif(trim==True):
            print("no trimmed version of impulse found, trimming...")
            if(trim ==True):
                window = cfg.trim_window
                impulse_abs = (np.abs(impulse[:, 0]) + np.abs(impulse[:, 1])).astype(np.double);
                intensity = np.zeros(impulse.shape[0] - window)
                for i in range(intensity.shape[0]):
                    intensity[i] = np.sqrt(np.sum(impulse_abs[i:i+window]**2))
                trigger = np.max(intensity)/cfg.trim_trigger
                for i in range(intensity.shape[0]):
                    k = intensity.shape[0] - i - 1
                    if intensity[k] > trigger:
                        if(k + window > impulse.shape[0]):
                            print("unable to trim file, lower the trigger maybe?")
                            cutoff = impulse.shape[0]
                        else:
                            cutoff = k + window
                            print("trimmed file from a length of", impulse.shape[0], "to a length of", cutoff)
                            impulse = impulse[0:cutoff, :]
                            wfo = wave.open(wave_file+"_trimmed.wav", 'wb')
                            wfo.setnchannels(2)
                            wfo.setsampwidth(2)
                            wfo.setframerate(44100)
                            wfo.writeframes(impulse.tobytes())
                        break
        return impulse
    
    def partition_filter(self, filter_length, height, n_cap, n_step):
        if height < 2**n_step - 1:
            height = 2**n_step - 1
        space_left = -filter_length
        buffers_needed = np.zeros(filter_length, dtype=np.int32)
        filter_size_in_buffers = np.zeros(filter_length, dtype=np.int32)
        filter_indices = np.zeros(filter_length + 1, dtype=np.int32)
        offsets = np.zeros(filter_length, dtype=np.int32) + self.first_filter_length
        i = 0
        n = cfg.n_start
        sum_of_previous_buffers = 0
        sum_of_previous_filters = 0
        previous_buffers_needed = 0
        previous_filter_size_in_buffers = 0
        while space_left < 0:
            buffers_needed[i] = 2**n
            filter_size_in_buffers[i] = (2**(cfg.power_ratio) - 1)*buffers_needed[i]
            space_left = space_left + filter_size_in_buffers[i]
            filter_indices[i + 1] = filter_size_in_buffers[i]*self.buffer + filter_indices[i] 
            sum_of_previous_filters += previous_filter_size_in_buffers
            if buffers_needed[i]!=previous_buffers_needed:
                sum_of_previous_buffers += buffers_needed[i] - previous_buffers_needed
            offsets[i] += sum_of_previous_filters - sum_of_previous_buffers + 1
            previous_buffers_needed = buffers_needed[i]
            previous_filter_size_in_buffers = filter_size_in_buffers[i]
            n += n_step*math.floor((i%height + 1)/height)
            if n > n_cap: n = n_cap
            i += 1
        
        filter_indices = filter_indices[0:i+1]
        self.buffers_needed = buffers_needed[0:i]
        self.filter_size_in_buffers = filter_size_in_buffers[0:i]
        self.transform_size = (self.buffers_needed + self.filter_size_in_buffers)*self.buffer
        self.rfft_size = self.transform_size//2 + 1
        self.block_sizes = self.buffers_needed*self.buffer
        self.offsets = offsets[0:i]
        self.number_of_filters = self.buffers_needed.shape[0]
        self.convolution_buffer_length = math.ceil(np.sum(self.filter_size_in_buffers)/self.buffers_needed[-1])*self.buffers_needed[-1]
        
        print("filter number\tbuffers needed\tfilter size\t\toffset")
        for i in range(self.number_of_filters):
            print(i, end="\t\t\t\t")
            print(buffers_needed[i], end="\t\t\t\t")
            print(filter_size_in_buffers[i], end="\t\t\t\t")
            print(offsets[i])
        return filter_indices
    
    def compute_filter_fft(self, impulse, buffers_needed, filter_indices):
        space_left = np.sum(self.filter_size_in_buffers) - math.ceil(impulse.shape[0]/self.buffer)
        zeros_to_add = (space_left + 1)*self.buffer - impulse.shape[0]%self.buffer
        impulse = np.append(impulse, np.zeros((zeros_to_add, self.channels), dtype=np.int16)).reshape(-1, self.channels)
        filter_fft = np.zeros((impulse.shape[0] + buffers_needed.shape[0], self.channels), dtype=np.cdouble)
        filter_indices_fft = np.zeros(filter_indices.shape[0], dtype=np.int32)
        for j in range(buffers_needed.shape[0]):
            fft_length = self.transform_size[j]
            part_of_impulse = impulse[filter_indices[j]:filter_indices[j+1], :]
            part_of_filter_fft = np.fft.rfft(part_of_impulse, fft_length, axis=0)
            filter_indices_fft[j+1] = filter_indices_fft[j] + part_of_filter_fft.shape[0]
            filter_fft[filter_indices_fft[j]:filter_indices_fft[j+1], :] = part_of_filter_fft
        return impulse, filter_fft, filter_indices_fft
        
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
        count_pb = count%self.buffers_needed[-1]
        index1 = (count_pb + 1 - n)*self.buffer
        index2 = (count_pb + 1)*self.buffer
        if index1 < 0:
            index1 = index1 + self.previous_buffers.shape[0]
            diff1 = self.previous_buffers.shape[0] - index1
            diff2 = n - diff1
            n_previous_buffers = np.zeros((n, self.buffer), dtype=np.int16)
            n_previous_buffers[0:diff1, :] = self.previous_buffers[index1:index1 + diff1, :]
            n_previous_buffers[diff1:diff1 + diff2, :] = self.previous_buffers[0:diff2, :]
        else:
            n_previous_buffers = self.previous_buffers[index1:index2, :]
        return n_previous_buffers
