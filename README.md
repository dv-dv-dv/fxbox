# fxbox
Compressor
The compressor implements the log domain configuration shown by Giannoulis et al. The log domain configuration is attractive because it allows for arbitrary an arbitrary static gain curve.

The gain computer, level detector, log to lienar, and linear to log system functions are implemented in Cython.

Convolver
The convolver implements a non uniformed partition convolution algorithm, an idea largely credited to Gardner and which Wefers summarizes the advances with these algorithms since Gardner's paper in 1995. This allows for real-time* convolution with impulse responses up to 5 seconds (200,000+ tap filters) running on the Raspberry Pi 4.

Some of the optimizations used in the convolver are: performing convolutions using FFT, performing FFTs using RFFTs, precomputing the FFTs of the impulse response, reusing previously computed FFTs of audio samples.

The main area where the convolver could be improved upon is by utilizing multiprocessing/multithreading but Python is not very good at multithreading.

Equalizer
The equalizer includes and lowpass, highpass, and two peaking filters. These lowpass and highpass are designed using the butter() function in SciPy. The peaking filter is designed by designing a bandpass filter and then adding the bandpass filter to an allpass filter with an option to apply gain in dB at the center frequency of the bandpass (0 db gain means that the peaking filter becomes an allpass filter).

The filtering is done by an algorithm implementing a direct II transpose structure which was coded and implemented using Cython.

* real-time meaning that an audio sample is processed and then given to the ADC within a single buffer.
References
[1] Digital Dynamic Range Compressor Design by D. Giannoulis, M. Massberg, J.D. Reiss
[2] Efficient Convolution without Input-Output Delay by W.G. Gardner
[3] Partitioned Convolution Algorithms for Real-timne Auralization by F. Wefers
