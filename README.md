# fxbox
Compressor

The compressor implements the log domain configuration shown by Giannoulis et al. The log domain configuration is attractive because it allows for arbitrary an arbitrary static gain curve.

The gain computer, level detector, log to linear, and linear to log system functions are implemented in Cython.

The compressor has the parameters of threshold, ratio, knee width, pre gain, post gain, attack, release, RMS, and hold.

Convolver

The convolver implements a non uniformed partition convolution algorithm, an idea largely credited to Gardner and which Wefers summarizes the advances with these algorithms since Gardner's paper in 1995. This allows for real-time* convolution with impulse responses up to 5 seconds (200,000+ tap filters) running on the Raspberry Pi 4.

The partitioning algorithm is a modification of Gardner's original algorithm, allowing for one to choose the partition height (how many times a specific filter size is repeated), the n step (an n step of 1 increases filter sizes at a rate 2^1, an n step of 2 increases filter sizes at a rate of 2^2), the first filter power (the size of the first filter represented as a power of 2), and a filter size cap (filters cannot be larger than this size). The height parameter allows for previously computer FFTs to be reused, the n step parameters allows the filter sizes to increase faster, the first filter power allows the filter sizes to start at a larger number, the filter size cap allows one to cap the filter sizes at the size that their computer can most efficiently compute FFTs.

Some of the optimizations used in the convolver are: performing convolutions using FFT, performing FFTs using RFFTs, precomputing the FFTs of the impulse response, reusing previously computed FFTs of audio samples.

The main area where the convolver could be improved upon is by utilizing multiprocessing/multithreading but Python is not very good at multithreading.

Equalizer

The equalizer includes and lowpass, highpass, and two peaking filters. These lowpass and highpass are designed using the butter() function in SciPy. The peaking filter is designed by designing a bandpass filter and then adding the bandpass filter to an allpass filter with an option to apply gain in dB at the center frequency of the bandpass (0 dB gain means that the peaking filter becomes an allpass filter).

The filtering is done by an algorithm implementing a direct II transpose structure which was coded and implemented using Cython.

References
[1] Digital Dynamic Range Compressor Design by D. Giannoulis, M. Massberg, J.D. Reiss

[2] Efficient Convolution without Input-Output Delay by W.G. Gardner

[3] Partitioned Convolution Algorithms for Real-time Auralization by F. Wefers

