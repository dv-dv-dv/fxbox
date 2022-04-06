import numpy as np
import math
import threading, queue
import time

# user imports
import config as cfg

class Convolver:
    class FilterFFT:
        def __init__(self, filter_partition, buffers_needed, offset, buffer_size, blength=-1):
            # blength: length in buffers
            if blength == -1: blength = buffers_needed*2
            self.buffers_needed = buffers_needed
            self.length = blength*buffer_size
            self.blength = blength
            self.rfft_length = self.length//2 + 1
            self.offset = offset
            self.filter_rfft = np.fft.rfft(filter_partition, self.length, axis=0)
            self.time_spent_doing_rffts = 0
            self.time_spent_doing_irffts = 0
        
        def convolve(self, audio_in):
            self.time_spent_doing_rffts -= time.perf_counter()
            audio_in_rfft = np.fft.rfft(audio_in, self.length, axis=0)
            self.time_spent_doing_rffts += time.perf_counter()
            self.time_spent_doing_irffts -= time.perf_counter()
            audio_out = np.fft.irfft(audio_in_rfft*self.filter_rfft, axis=0)
            self.time_spent_doing_irffts += time.perf_counter()
            return audio_out
        
        def convolve_rfft(self, audio_in_rfft):
            self.time_spent_doing_irffts -= time.perf_counter()
            audio_out = np.fft.irfft(audio_in_rfft*self.filter_rfft, axis=0)
            self.time_spent_doing_irffts += time.perf_counter()
            return audio_out
        
    def __init__(self, impulse_number=1, realtime=False):
        print("initializing convoler...")
        self.buffer = cfg.buffer
        self.parallel_max = cfg.parallel_max
        impulse = self.import_from_wave("impulses/" + cfg.imps[impulse_number])
        self.channels = 2 # only two channels is verified to be working
        self.set_impulse(impulse)
        self.realtime=realtime
        self.count = 0
        self.abs_count = 0
        self.number_of_rffts = 0
        self.number_of_irffts = 0
        self.time_spent_doing_rffts = 0
        self.time_spent_doing_irffts = 0
        self.time_spent_in_convolver = 0
        self.time_spent_in_add_to_convolution_buffer = 0
        self.time_spent_in_get_from_convolution_buffer = 0
        if(self.complex_convolution == True):
            self.time_spent_in_get_n_previous_buffers = 0
            self.time_spent_doing_complex_convolution = 0
            self.convolution_queue = queue.PriorityQueue(-1)
            self.worker_process = threading.Thread(target=self.convolution_worker, daemon=True)
            self.worker_process.start()
        
    def print_performance_stats(self):
        print("number of rffts:", self.number_of_rffts)
        print("number of irffts:", self.number_of_irffts)
        print("total number of rffts and irffts:", self.number_of_rffts + self.number_of_irffts)
        print("time spent doing rffts:", round(self.time_spent_doing_rffts, 4))
        print("time spent doing irffts:", round(self.time_spent_doing_irffts, 4))
        print("total time spent doing rffts and irffts:", round(self.time_spent_doing_rffts + self.time_spent_doing_irffts, 4))
        print("time spent in add to convolution buffer", round(self.time_spent_in_add_to_convolution_buffer, 4))
        print("time spent in get grom convolution buffer", round(self.time_spent_in_get_from_convolution_buffer, 4))
        if(self.complex_convolution==True):
            print("time spent in get n previous buffers", round(self.time_spent_in_get_n_previous_buffers, 4))
            print("time spent scheduling convolutions", round(self.time_spent_doing_complex_convolution, 4))
        print("total time spent in convolver", round(self.time_spent_in_convolver, 4))
        print("ratio of time spent doing rffts and irffts and time spent in convolver", round((self.time_spent_doing_irffts + self.time_spent_doing_rffts)/self.time_spent_in_convolver, 4))
        
    # this function does the necessary work in order to get the impulse ready for use
    def set_impulse(self, impulse):
        # set first filter
        first_filter_blength = 2**cfg.first_filter_power - 1
        first_filter_length = self.buffer*(2**cfg.first_filter_power - 1)
        first_filter = impulse[0:first_filter_length, :]
        self.first_filter = self.FilterFFT(first_filter, 1, 0, self.buffer, blength=first_filter_blength + 1)
        if(impulse.shape[0] > first_filter_length): 
            impulse = impulse[first_filter_length: impulse.shape[0] - 1, :]
            self.complex_convolution = True
            filter_length = math.ceil(impulse.shape[0]/self.buffer)
            n_step = cfg.n_step
            height = cfg.height
            n_cap = math.floor(math.log2(cfg.filter_size_cap/self.buffer))
            (buffers_needed, filter_size_in_buffers, filter_indices, offsets, convolution_buffer_length) = self.partition_filter(first_filter_blength, filter_length, height, n_cap, n_step)
            filt = np.empty(buffers_needed.shape[0], dtype=object)
            for i in range(buffers_needed.shape[0]):
                impulse_partition = impulse[filter_indices[i]:filter_indices[i+1], :]
                filt[i] = self.FilterFFT(impulse_partition, buffers_needed[i], offsets[i], self.buffer)
            self.filt = filt
            self.max_buffers_needed = buffers_needed[-1]
            self.buffers_needed = buffers_needed
            self.number_of_filters = buffers_needed.shape[0]
            self.convolution_buffer_length = convolution_buffer_length
            self.previous_buffers = np.zeros((self.buffer*buffers_needed[-1], self.channels), dtype=np.int16)
            self.convolution_buffer = np.zeros((convolution_buffer_length*self.buffer, self.channels), dtype=np.double)
        else:
            print("impulse is short, disabling advanced convolver features")
            self.complex_convolution = False
            self.convolution_buffer = np.zeros((4*first_filter_length, self.channels), dtype=np.double)
            self.convolution_buffer_length = 4*first_filter_blength
    
    def partition_filter(self, first_filter_blength, filter_length, height, n_cap, n_step):
        if height < 2**n_step - 1:
            height = 2**n_step - 1
        space_left = -filter_length
        buffers_needed = np.zeros(filter_length, dtype=np.int32)
        filter_size_in_buffers = np.zeros(filter_length, dtype=np.int32)
        filter_indices = np.zeros(filter_length + 1, dtype=np.int32)
        offsets = np.zeros(filter_length, dtype=np.int32) + first_filter_blength
        i = 0
        n = cfg.n_start
        sum_of_previous_buffers = 0
        sum_of_previous_filters = 0
        previous_buffers_needed = 0
        previous_filter_size_in_buffers = 0
        while space_left < 0:
            buffers_needed[i] = 2**n
            filter_size_in_buffers[i] = buffers_needed[i]
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
        buffers_needed = buffers_needed[0:i]
        filter_size_in_buffers = filter_size_in_buffers[0:i]
        transform_sizes = (buffers_needed + filter_size_in_buffers)*self.buffer
        offsets = offsets[0:i]
        convolution_buffer_length = math.ceil(np.sum(filter_size_in_buffers)/buffers_needed[-1])*buffers_needed[-1]
        
        print("filter number\tbuffers needed\tfilter size\t\toffset")
        for i in range(buffers_needed.shape[0]):
            print(i, end="\t\t\t\t")
            print(buffers_needed[i], end="\t\t\t\t")
            print(filter_size_in_buffers[i], end="\t\t\t\t")
            print(offsets[i])
        return buffers_needed, filter_size_in_buffers, filter_indices, offsets, convolution_buffer_length
    
    def convolve(self, audio_in):
        self.time_spent_in_convolver -= time.perf_counter()
        if(self.complex_convolution == True):
            self.time_spent_doing_complex_convolution -= time.perf_counter()
            bufferpos = self.buffer*(self.count%self.max_buffers_needed)
            self.previous_buffers[bufferpos:bufferpos + self.buffer, :] = audio_in
            for i in range(self.number_of_filters):
                if (self.count + 1)%self.filt[i].buffers_needed != 0: break
                self.convolution_queue.put((self.abs_count + self.filt[i].offset, self.count, i))
            self.time_spent_doing_complex_convolution += time.perf_counter()
            
            if self.realtime==False:
                self.convolution_queue.join()
                
        self.add_to_convolution_buffer(self.first_filter.convolve(audio_in), 0, self.count)
        audio_in2 = audio_in.astype(np.double)
        audio_out = cfg.post*(cfg.wet*self.get_from_convolution_buffer() + cfg.dry*0.5*audio_in2)
        self.abs_count += 1
        self.count = (self.abs_count)%self.convolution_buffer_length
        self.time_spent_in_convolver += time.perf_counter()
        return audio_out.astype(np.int16)
    
    def convolution_worker(self):
        class spectra:
            def __init__(self):
                self.spectra = None
                self.count = -1
                self.buffers_needed = -1
            
        unique_blocks = np.unique(self.buffers_needed)
        unique_spectras = unique_blocks.shape[0]
        prev_buffers_needed = -1
        prev_count = -1
        spectras = np.empty(unique_spectras, dtype=object)
        filt = self.filt
        for i in range(unique_spectras):
            spectras[i] = spectra()
            spectras[i].buffers_needed = unique_blocks[i]
        while True:
            spectra_needed = True
            (deadline, count, i) = self.convolution_queue.get()
            if(deadline > self.abs_count):
                # determine if an rfft was previously calculated for this audio sample
                if (filt[i].buffers_needed!=prev_buffers_needed)|(count!=prev_count):
                    for j in range(unique_spectras):
                        if spectras[j].buffers_needed==filt[i].buffers_needed:
                            index = j
                            if(spectras[j].count==count):
                                audio_to_filter_rfft = spectras[j].spectra
                                spectra_needed = False
                            break

                    if(spectra_needed==True):
                        audio_to_filter = self.get_n_previous_buffers(filt[i].buffers_needed, count)
                        self.time_spent_doing_rffts -= time.perf_counter()
                        audio_to_filter_rfft = np.fft.rfft(audio_to_filter, filt[i].length, axis=0)
                        self.time_spent_doing_rffts += time.perf_counter()
                        spectras[index].spectra = audio_to_filter_rfft
                        spectras[index].count = count
                        self.number_of_rffts += 1

                prev_buffers_needed = filt[i].buffers_needed
                prev_count = count
                self.add_to_convolution_buffer(filt[i].convolve_rfft(audio_to_filter_rfft), filt[i].offset, count)
            else: print("convolution of size", filt[i].buffers_needed, "was dropped")
            self.convolution_queue.task_done()
            
    def get_from_convolution_buffer(self):
        self.time_spent_in_get_from_convolution_buffer -= time.perf_counter()
        index1 = (self.count)*self.buffer
        index2 = (self.count + 1)*self.buffer
        audio_out = 0.5*self.convolution_buffer[index1:index2, :]/2**15
        self.convolution_buffer[index1:index2, :] = 0
        self.time_spent_in_get_from_convolution_buffer += time.perf_counter()
        return audio_out

    def add_to_convolution_buffer(self, audio_in, offset, count):
        self.time_spent_in_add_to_convolution_buffer -= time.perf_counter()
        index1 = ((count + offset)%self.convolution_buffer_length)*self.buffer
        index2 = index1 + audio_in.shape[0]
        if index2 > self.convolution_buffer.shape[0]:
            diff1 = self.convolution_buffer.shape[0] - index1
            diff2 = audio_in.shape[0] - diff1
            self.convolution_buffer[index1:index1 + diff1, :] += audio_in[0:diff1, :]
            self.convolution_buffer[0:diff2, :] += audio_in[diff1:diff1 + diff2, :]
        else:
            self.convolution_buffer[index1:index2, :] += audio_in
        self.time_spent_in_add_to_convolution_buffer += time.perf_counter()

    def get_n_previous_buffers(self, n, count):
        self.time_spent_in_get_n_previous_buffers -= time.perf_counter()
        count_pb = count%self.max_buffers_needed
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
        self.time_spent_in_get_n_previous_buffers += time.perf_counter()
        return n_previous_buffers
    
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
        print(np.max(impulse))
        print("impulse is", round(impulse.shape[0]/44100, 2), "seconds long")
        if((impulse.shape[0]>100000)&cfg.trim):
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
                            print("impulse is", round(impulse.shape[0]/44100, 2), "seconds long")
                        break
        return impulse
