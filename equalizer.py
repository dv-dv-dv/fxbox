import numpy as np

# user imports
import config as cfg
import equalizer_cy
class Equalizer:        
    class Filter:
        # for lowpass and highpass you need
        # N - filter order, fc - cutoff frequency (highpass and lowpass only), btype - filter type,
        # for peaking you need
        # N filter order, fgm - geometric mean (center frequency), bfac - bandwidth as a multiple of fgm, gdb - gain at fgm in decibels
        def __init__(self, N=None, fc=None, fgm=None, bfac=None, btype=None, gdb=None, samplerate=cfg.samplerate):
            import scipy.signal as sps
            if bfac!=None:
                R = 0.5*(bfac + np.sqrt(bfac**2 + 4))
                g = 10**(gdb/20) - 1
                f1 = fgm*R
                f2 = fgm/R
                if f1 > samplerate/2: f1 = samplerate/2 - 1
                b_temp, a = sps.butter(N=N, Wn=[f2, f1], fs=samplerate, btype=btype)
                b = a + g*b_temp
                self.N, self.fgm, self.f1, self.f2, self.bfac, self.gdb = N, fgm, f1, f2, bfac, gdb
                print("b: " + str(b) + "\na:" + str(a))
            else:
                b, a = sps.butter(N=N, Wn=fc, fs=samplerate, btype=btype)
                self.N, self.fc, self.btype = N, fc, btype
            
            self.a = a
            self.b = b
            self.a_flipped = np.flip(a)
            self.b_flipped = np.flip(b)
            self.nm_max = max(a.shape[0], b.shape[0]) - 1
            self.x = np.zeros((cfg.buffer_size + self.nm_max, 2), np.double)
            self.y = np.zeros((cfg.buffer_size + self.nm_max, 2), np.double)
            self.btype = btype
        
        def filter_audio(self, audio_in):
            audio_out, self.x, self.y = equalizer_cy.filter_audio(audio_in, self.a_flipped, self.b_flipped, self.nm_max, self.x, self.y)
            return audio_out
        
        def plot_freq_response(self):
            import matplotlib.pyplot as plt
            import scipy.signal as sps
            w, h = sps.freqz(self.b, self.a, fs=44100)
            plt.semilogx(w, 20*np.log10(abs(h)))
            if self.btype=='bandpass':
                title = 'bell, fgm=' + str(self.fgm) + 'Hz, Q=' + str(1/self.bfac) +', N=' + str(2*self.N) + ', gain=' + str(self.gdb) +'dB'
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
                plt.axvline(self.f1, color='green')
                plt.axvline(self.f2, color='green') 
            else:
                plt.axvline(self.fc, color='green')
            
            plt.show()
        
    def __init__(self, lpf_fc=None, lpf_N=None, lpf_en=None, hpf_fc=None, hpf_N=None, hpf_en=None, bll1_fgm=None, bll1_N=None, bll1_bfac=None, bll1_gdb=None, bll1_en=None, bll2_fgm=None, bll2_N=None, bll2_bfac=None, bll2_gdb=None, bll2_en=None):
        # self.bll_vec = self.Filter()
        self.update_params(cfg.lpf_fc, cfg.lpf_N, cfg.lpf_en, cfg.hpf_fc, cfg.hpf_N, cfg.hpf_en, cfg.bll1_fgm, cfg.bll1_N, cfg.bll1_bfac, cfg.bll1_gdb, cfg.bll1_en, cfg.bll2_fgm, cfg.bll2_N, cfg.bll2_bfac, cfg.bll2_gdb, cfg.bll2_en, reinit=False)
        self.update_params(lpf_fc, lpf_N, lpf_en, hpf_fc, hpf_N, hpf_en, bll1_fgm, bll1_N, bll1_bfac, bll1_gdb, bll1_en, bll2_fgm, bll2_N, bll2_bfac, bll2_gdb, bll2_en)
        
    def update_params(self, lpf_fc=None, lpf_N=None, lpf_en=None, hpf_fc=None, hpf_N=None, hpf_en=None, bll1_fgm=None, bll1_N=None, bll1_bfac=None, bll1_gdb=None, bll1_en=None, bll2_fgm=None, bll2_N=None, bll2_bfac=None, bll2_gdb=None, bll2_en=None, reinit=True):
        if lpf_fc != None:
            self.lpf_fc = lpf_fc
            self.update_lpf = True
        if lpf_N != None:
            self.lpf_N = lpf_N
            self.update_lpf = True
        if lpf_en != None:
            self.lpf_en = lpf_en
        if hpf_fc != None:
            self.hpf_fc = hpf_fc
            self.update_hpf = True
        if hpf_N != None:
            self.hpf_N = hpf_N
            self.update_hpf = True
        if hpf_en != None:
            self.hpf_en = hpf_en
        if bll1_fgm != None:
            self.bll1_fgm = bll1_fgm
            self.update_bll1 = True
        if bll1_N != None:
            self.bll1_N = bll1_N
            self.update_bll1 = True
        if bll1_bfac != None:
            self.bll1_bfac = bll1_bfac
            self.update_bll1 = True
        if bll1_gdb != None:
            self.bll1_gdb = bll1_gdb
            self.update_bll1 = True
        if bll1_en != None:
            self.bll1_en = bll1_en
        if bll2_fgm != None:
            self.bll2_fgm = bll2_fgm
            self.update_bll2 = True
        if bll2_N != None:
            self.bll2_N = bll2_N
            self.update_bll2 = True
        if bll2_bfac != None:
            self.bll2_bfac = bll2_bfac
            self.update_bll2 = True
        if bll2_gdb != None:
            self.bll2_gdb = bll2_gdb
            self.update_bll2 = True
        if bll2_en != None:
            self.bll2_en = bll2_en
        if reinit==True: 
            self.update_filters()
    def print_params(self):
        print("lpf: fc=" + str(self.lpf_fc) + " N=" + str(self.lpf_N) + " en=" + str(self.lpf_en))
        print("hpf: fc=" + str(self.hpf_fc) + " N=" + str(self.hpf_N) + " en=" + str(self.hpf_en))
        print("bll1: fgm=" + str(self.bll1_fgm) + " N=" + str(self.bll1_N) + " bfac=" + str(self.bll1_bfac) + " gdb=" + str(self.bll1_gdb) +" en=" + str(self.bll1_en))
        print("bll2: fgm=" + str(self.bll2_fgm) + " N=" + str(self.bll2_N) + " bfac=" + str(self.bll2_bfac) + " gdb=" + str(self.bll2_gdb) +" en=" + str(self.bll2_en))

    def update_filters(self):
        if self.update_lpf == True:
            self.lpf = self.Filter(fc=self.lpf_fc, N=self.lpf_N, btype='lowpass')
        if self.update_hpf == True:
            self.hpf = self.Filter(fc=self.hpf_fc, N=self.hpf_N, btype='highpass')
        if self.update_bll1 == True:
            self.bll1 = self.Filter(fgm=self.bll1_fgm, N=self.bll1_N, bfac=self.bll1_bfac, gdb=self.bll1_gdb, btype='bandpass')
        if self.update_bll2 == True:
            self.bll2 = self.Filter(fgm=self.bll2_fgm, N=self.bll2_N, bfac=self.bll2_bfac, gdb=self.bll2_gdb, btype='bandpass')
        # self.print_params()
        self.update_lpf, self.update_hpf, self.update_bll1, self.update_bll2 = False, False, False, False
        
    def equalize(self, audio_in):
        audio_out = audio_in
        if self.lpf_en == 1:
            audio_out = self.lpf.filter_audio(audio_out)
        if self.hpf_en == 1:
            audio_out = self.hpf.filter_audio(audio_out)
        if self.bll1_en == 1:
            audio_out = self.bll1.filter_audio(audio_out)
        if self.bll2_en == 1:
            audio_out = self.bll2.filter_audio(audio_out)
        return audio_out

def main():
    eq = Equalizer(bll1_gdb=-8)
    # eq.lpf.plot_freq_response()
    # eq.hpf.plot_freq_response()
    eq.bll1.plot_freq_response()
    for i in range(-12, 12):
        eq = Equalizer(bll1_bfac=1, bll1_gdb=i)
        eq.bll1.plot_freq_response()

if __name__ == "__main__":
    main()