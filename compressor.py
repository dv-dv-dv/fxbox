import numpy as np
import math

# user imports
import config as cfg
import compressor_cy

class Compressor:
    def __init__(self, threshold=None, ratio=None, knee_width=None, pre_gain=None, post_gain=None, attack=None, release=None, rms=None, hold=None):
        self.update_params(cfg.threshold, cfg.ratio, cfg.knee_width, cfg.pre_gain, cfg.post_gain, cfg.attack, cfg.release, cfg.rms, cfg.hold, reinit=False)
        self.update_params(threshold, ratio, knee_width, pre_gain, post_gain, attack, release, rms, hold)
        self.update_compressor()
        
    def update_params(self, threshold=None, ratio=None, knee_width=None, pre_gain=None, post_gain=None, attack=None, release=None, rms=None, hold=None, reinit=True):
        if threshold != None: 
            self.threshold = threshold
        if ratio != None: 
            self.ratio = ratio
        if knee_width != None: 
            self.knee_width = knee_width
        if pre_gain != None: 
            self.pre_gain = pre_gain
        if post_gain != None: 
            self.post_gain = post_gain
        if attack != None: 
            self.attack = attack
        if release != None: 
            self.release = release
        if rms != None:
            self.rms = rms
        if hold != None:
            self.hold = hold
        if reinit == True:
            self.update_compressor()
            
    def update_compressor(self):
        self.comp = compressor_cy.Compressor(self.threshold, self.ratio, self.knee_width, self.pre_gain, self.post_gain, self.attack, self.release, self.rms, self.hold)
        
    def compress(self, audio_in):
        audio_in_mono = (audio_in[:, 0] + audio_in[:, 1])/2
        gain_linear = self.calculate_gain(audio_in_mono)
        audio_out = audio_in
        audio_out[:, 0] *= gain_linear
        audio_out[:, 1] *= gain_linear
        return audio_out
    
    def calculate_gain(self, audio_in):
        actual_db = self.comp.linear_to_log(audio_in)
        desired_db = self.comp.gain_computer(actual_db)
        diff_db = actual_db - desired_db
        smooth_diff_db = self.comp.level_detector(diff_db)
        gain_in_db = self.post_gain - smooth_diff_db
        gain_linear = self.comp.log_to_linear(gain_in_db)
        return gain_linear
    
def main():
    # plot static gain
    import matplotlib.pyplot as plt
    comp = Compressor(knee_width=50, rms=True, post_gain=0)
    db_vals = 100*np.arange(-256, 0)/256
    gc_out = comp.comp.gain_computer(db_vals)
    test = 7
    
    fig, ax = plt.subplots()
    ax.plot(db_vals, gc_out, linewidth=2.0)
    plt.show()
    
    # plot level detector
    ld_test0 = 0*np.ones(256)
    ld_test1 = 5*np.ones(256)
    a, b, c = 1, 2, 20
    ld_out = np.zeros(1)
    test = comp.comp.level_detector(ld_test0)
    while test[0] > 0.01:
        test = comp.comp.level_detector(ld_test0)
    for __ in range(a):
        ld_out = np.append(ld_out, comp.comp.level_detector(ld_test0))
    for __ in range(b):
        ld_out = np.append(ld_out, comp.comp.level_detector(ld_test1))
    for __ in range(c):
        ld_out = np.append(ld_out, comp.comp.level_detector(ld_test0))
    ld_testx = np.arange(0, (a+b+c)*256)
    fig, ax = plt.subplots()
    ax.plot(ld_testx, ld_out[1:ld_out.shape[0]], linewidth=2.0)
    ax.set(ylim=(0, 10))
    plt.show()
    
if __name__ == "__main__":
    main()