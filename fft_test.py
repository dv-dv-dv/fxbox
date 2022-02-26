
import numpy as np
from numpy import fft
import time

def test1(audio_sample):
    global buffer, n_cap, n_step, min_tests
    time_data = np.zeros((n_cap, n_cap))
    width = audio_sample.shape[1]
    for i in range(n_cap):
        tests = min_tests*2**(i)
        for j in range(0, i+1):
            block_factor = 2**j
            start = time.perf_counter()
            number_of_points = 2*buffer*block_factor//width
            random_ints = np.random.randint(0, audio_sample.shape[0]-1, tests//block_factor, dtype=np.int32)
            
            for k in range(tests//block_factor):
                test_sample = audio_sample[random_ints[k]:random_ints[k] + buffer*block_factor//width]
                a = fft.rfft(test_sample, number_of_points, axis=0)
                b = fft.irfft(test_sample, number_of_points, axis=0)
            time_data[i, j] = time.perf_counter() - start
            

    return time_data

buffer = 64
n_cap = 12
n_step = 1
audio_sample = np.random.randint(1 - 2**15, 2**15, (buffer*(2**n_cap)*2, 1), dtype=np.int16)
parallel_max = 5
min_tests = 2**parallel_max
time_data = np.zeros((n_cap, n_cap, parallel_max))
for i in range(parallel_max):
    time_data[: ,: , i] = test1(audio_sample.reshape(-1,2**i))
    
for k in range(parallel_max):
    for i in range(n_cap):
        samples_processed = buffer*2**(i)
        sort = np.argsort(time_data[i, 0:i+1, k])[0]
        print("fastest time to process", samples_processed, "samples was", time_data[i, sort, k]*1000, "milliseconds with a ", buffer*2**sort, "point rfft")
# test1(audio_sample)
# test1(audio_sample.reshape(-1,2))
# test1(audio_sample.reshape(-1,4))
# test1(audio_sample.reshape(-1,8))