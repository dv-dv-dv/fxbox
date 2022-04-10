import numpy as np


# user imports
import config as cfg
import equalizer_cy
class Equalizer:        
    class Filter:
        # for lowpass and highpass you need
        # N - filter order, fc - cutoff frequency (highpass and lowpass only), btype - filter type,
        # for peaking you need
        # N filter order, fgm - geometric mean (center frequency), bfac - bandwidth as a factor of fgm, k - gain
        def __init__(self, N=None, fc=None, fgm=None, bfac=None, btype=None, gdb=None, samplerate=cfg.samplerate):
            import scipy.signal as sps
            if btype=='bandpass':
                R = 0.5*(bfac + np.sqrt(bfac**2 + 4))
                g = 10**(gdb/20) - 1
                f1 = fgm*R
                f2 = fgm/R
                if f1 > samplerate/2: f1 = samplerate/2 - 1
                b_temp, a = sps.butter(N=N, Wn=[f1, f2], fs=samplerate, btype=btype)
                b = a + g*b_temp
                self.N, self.fgm, self.f1, self.f2, self.bfac, self.gdb = N, fgm, f1, f2, bfac, gdb
            else:
                b, a = sps.butter(N=N, Wn=fc, fs=samplerate, btype=btype)
                self.N, self.fc, self.btype = N, fc, btype
            
            self.filt = equalizer_cy.Equalizer(b, a)
            self.a = a
            self.b = b
            self.btype = btype
        
        def filter_audio(self, audio_in):
            return self.filt.filter_audio(audio_in)
        
        def plot_freq_response(self):
            import matplotlib.pyplot as plt
            import scipy.signal as sps
            w, h = sps.freqz(self.b, self.a, fs=44100)
            plt.semilogx(w, 20*np.log10(abs(h)))
            if self.btype=='bandpass':
                title = 'bell, fgm=' + str(self.fgm) + 'Hz, Q=' + str(1/self.bfac) +', N=' + str(self.N) + ', gain=' + str(self.gdb) +'dB'
            else:
                title = self.btype + ', fc=' + str(self.fc) + 'Hz, N=' + str(self.N)
            plt.title(title)
            plt.xlabel('Frequency [Hz]')
            plt.xlim([20, 20000])
            plt.ylabel('Amplitude [dB]')
            plt.ylim([-12, 12])
            plt.margins(0, 0.1)
            plt.grid(which='both', axis='both')
            if self.btype=='bandpass':
                plt.axvline(self.f1, color='green') # cutoff frequency
                plt.axvline(self.f2, color='green') # cutoff frequency
            else:
                plt.axvline(self.fc, color='green') # cutoff frequency
            plt.show()
        
    def __init__(self, lpf_fc=None, lpf_N=None, lpf_en=None, hpf_fc=None, hpf_N=None, hpf_en=None, bll_fgm=None, bll_N=None, bll_bfac=None, bll_gdb=None, bll_en=None):
        # self.bll_vec = self.Filter()
        self.update_params(cfg.lpf_fc, cfg.lpf_N, cfg.lpf_en, cfg.hpf_fc, cfg.hpf_N, cfg.hpf_en, cfg.bll_fgm, cfg.bll_N, cfg.bll_bfac, cfg.bll_gdb, cfg.bll_en, reinit=False)
        self.update_params(lpf_fc, lpf_N, lpf_en, hpf_fc, hpf_N, hpf_en, )
        
    def update_params(self, lpf_fc=None, lpf_N=None, lpf_en=None, hpf_fc=None, hpf_N=None, hpf_en=None, bll_fgm=None, bll_N=None, bll_bfac=None, bll_gdb=None, bll_en=None, reinit=True):
        if lpf_fc != None:
            self.lpf_fc = lpf_fc
        if lpf_N != None:
            self.lpf_N = lpf_N
        if lpf_en != None:
            self.lpf_en = lpf_en
        if hpf_fc != None:
            self.hpf_fc = hpf_fc
        if hpf_N != None:
            self.hpf_N = hpf_N
        if hpf_en != None:
            self.hpf_en = hpf_en
        if bll_fgm != None:
            self.bll_fgm = bll_fgm
        if bll_N != None:
            self.bll_N = bll_N
        if bll_bfac != None:
            self.bll_bfac = bll_bfac
        if bll_gdb != None:
            self.bll_gdb = bll_gdb
        if bll_en != None:
            self.bll_en = bll_en
        if reinit==True: 
            self.update_filters()
        
    def update_filters(self):
        self.lpf = self.Filter(fc=self.lpf_fc, N=self.lpf_N, btype='lowpass')
        self.hpf = self.Filter(fc=self.hpf_fc, N=self.hpf_N, btype='highpass')
        self.bll = self.Filter(fgm=self.bll_fgm, N=self.bll_N, bfac=self.bll_bfac, gdb=self.bll_gdb, btype='bandpass')
        
    def equalize(self, audio_in):
        audio_out = audio_in
        if self.lpf_en == True:
            audio_out = self.lpf.filter_audio(audio_out)
        if self.hpf_en == True:
            audio_out = self.hpf.filter_audio(audio_out)
        if self.bll_en == True:
            audio_out = self.bll.filter_audio(audio_out)
        return audio_out

def main():
    eq = Equalizer()
    eq.lpf.plot_freq_response()
    eq.hpf.plot_freq_response()
    eq.bll.plot_freq_response()

if __name__ == "__main__":
    main()