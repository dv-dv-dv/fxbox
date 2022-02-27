def generate_wisdom(start_n, stop_n, max_width, max_threads):
    import numpy as np
    import pyfftw
    audio_sample = np.random.randint(1 - 2**15, 2**15,(2**(14+2), 1), dtype=np.int16)
    for k in range(max_threads):
        threads = k + 1
        for j in range(max_width):
            width = j + 1
            print("generating for width of", width)
            for i in range(start_n, stop_n + 1):
                a = pyfftw.empty_aligned((2**(i), width), dtype='float32')
                b = pyfftw.empty_aligned((2**(i - 1) + 1, width), dtype='complex64')
                c = pyfftw.empty_aligned((2**(i), width), dtype='float32')
                frfft = pyfftw.FFTW(a, b, axes=(0,), flags=('FFTW_MEASURE',), threads=threads)
                brfft = pyfftw.FFTW(b, c, axes=(0,), direction='FFTW_BACKWARD', flags=('FFTW_MEASURE',), threads=threads)
                print("wisdom for", 2**(i), "transform generated")
    import pickle
    wisdom = pyfftw.export_wisdom()
    pickle.dump(wisdom, open('wisdom.dump', 'wb'))
    return wisdom
            
def check_for_wisdom():
    import os.path
    if(os.path.exists("wisdom.dump")):
        return True
    else:
        return False
    
def get_wisdom():
    if check_for_wisdom()==True:
        import pyfftw
        import pickle
        wisdom = pickle.load(open('wisdom.dump', 'rb'))
        pyfftw.import_wisdom(wisdom)
        wisdom = generate_wisdom(4,17,2,4)
    else:
        print("no wisdom available, generating wisdom")
        wisdom = generate_wisdom(4,17,2,4)
    return wisdom
    
def main():
    check_for_wisdom()
    generate_wisdom(4, 16, 2)
    check_for_wisdom()

if __name__ == "__main__":
    main()