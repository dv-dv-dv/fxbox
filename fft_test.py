
import numpy as np
from numpy import fft
import time
buffer = 64
n_cap = 12
n_step = 1
audio_sample = np.random.randint(1 - 2**15, 2**15, buffer*(2**n_cap)*2, dtype=np.int16)
min_tests = 10
time_data = np.zeros((n_cap, n_cap))
for i in range(n_cap):
    tests = min_tests*2**(i)
    for j in range(0, i+1):
        block_factor = 2**j
        start = time.perf_counter()
        for k in range(tests//block_factor):
            a = fft.rfft(audio_sample[0:buffer*block_factor], 2*buffer*block_factor, axis=0)
            b = fft.irfft(audio_sample[0:buffer*block_factor],2*buffer*block_factor, axis=0)
        time_data[i, j] = time.perf_counter() - start
        
for i in range(n_cap):
    samples_processed = buffer*min_tests*2**(i)
    sort = np.argsort(time_data[i, 0:i+1])
    print("fastest time to process", samples_processed, "samples was", time_data[i, sort[0]]*1000, "milliseconds with a ", buffer*2**sort[0], "point rfft")