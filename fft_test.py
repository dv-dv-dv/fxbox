
import numpy as np
import time

def fft_test(min_tests=100, n_min=6, n_max=10, min_channels=2, max_channels=6):
    for k in range(min_channels, max_channels+1):
        channels = k
        length_to_test = min_tests*2**n_max
        length_to_test2 = length_to_test*channels
        sample = np.random.randint(-2**14, 2**14, (min_tests*2**(n_max+1), channels))
        offsets = np.random.randint(0, sample.shape[0] - 2**(n_max), length_to_test)
        times = np.zeros(n_max + 1 - n_min)
        print("channels:",channels)
        for i in range(n_min, n_max + 1):
            t = 0
            transform_length = 2**i
            tests_to_run = length_to_test//transform_length
            t -= time.perf_counter_ns()
            e = 0
            print("testing transforms of length", transform_length)
            for j in range(tests_to_run):
                e -= time.perf_counter_ns()
                a = np.fft.rfft(sample[offsets[i]:offsets[i] + transform_length, :], axis=0)
                e += time.perf_counter_ns()
                b = np.fft.irfft(a)
            t += time.perf_counter_ns()
            times[i - n_min] = t - e
        for i in range(times.shape[0]):
            print("for a transform of length", 2**(n_min + i), "it takes",round(times[i]/length_to_test2, 2), "nanoseconds per sample")
        times_sorted_args = np.argsort(times)
        print("the fastest transform was a transform of length", 2**(n_min + times_sorted_args[0]), "which took", round(times[times_sorted_args[0]]/length_to_test2, 2), "nanoseconds per sample")

def main():
    fft_test()
    
if __name__ == "__main__":
    main()
