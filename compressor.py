import numpy as np
import math

# user imports
import config as cfg
import compressor_cy

class Compressor:
    class WriteArray:
        def __init__(self, file_name):
            self.f = open(file_name + '.txt', 'w')
            
        def write_array(self, array):
            for i in array:
                self.f.write(str(round(i, 3)) + "\n")
                
    def __init__(self, threshold=None, ratio=None, knee_width=None, pre_gain=None, post_gain=None, attack=None, release=None, log_gains=False):
        self.threshold = cfg.threshold 
        self.ratio = cfg.ratio
        self.knee_width = cfg.knee_width 
        self.pre_gain = cfg.pre_gain 
        self.post_gain = cfg.post_gain 
        self.attack = cfg.attack
        self.release = cfg.release
        self.log_gains = log_gains
        self.gain_logger = self.WriteArray('gain_log')
        self.update_params(threshold, ratio, knee_width, pre_gain, post_gain, attack, release)
        
    def create_compressor(self):
        self.comp = compressor_cy.Compressor(self.threshold, self.ratio, self.knee_width, self.pre_gain, self.post_gain, self.attack, self.release)
        
    def update_params(self, threshold=None, ratio=None, knee_width=None, pre_gain=None, post_gain=None, attack=None, release=None):
        if threshold is not None: 
            self.threshold = threshold
        if ratio is not None: 
            self.ratio = ratio
        if knee_width is not None: 
            self.knee_width = knee_width
        if pre_gain is not None: 
            self.pre_gain = pre_gain
        if post_gain is not None: 
            self.post_gain = post_gain
        if attack is not None: 
            self.attack = attack
        if release is not None: 
            self.release = release
        self.create_compressor()
        
    def print_params(self):
        print("threshold is", self.threshold)
        print("ratio is", self.ratio)
        print("knee_width is", self.knee_width)
        print("pre_gain is", self.pre_gain)
        print("post_gain is", self.post_gain)
        print("attack is", self.attack)
        print("release is", self.release)
        
    def compress(self, audio_in):
        audio_in_mono = (audio_in[:, 0] + audio_in[:, 1])/2
        gain_linear = self.calculate_gain(audio_in_mono)
        audio_out = audio_in
        audio_out[:, 0] *= gain_linear
        audio_out[:, 1] *= gain_linear
        if self.log_gains is True:
            self.gain_logger.write_array(gain_linear)
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
    comp = Compressor()
    db_vals = 100*np.arange(-256, 0)/256
    gc_out = comp.comp.gain_computer(db_vals)
    test = 7
    
    fig, ax = plt.subplots()
    ax.plot(db_vals, gc_out, linewidth=2.0)
    plt.show()
    
    ld_test0 = -40*np.ones(256)
    ld_test1 = -20*np.ones(256)
    a, b, c = 2, 2, 20
    ld_out = np.zeros(1)
    for __ in range(a):
        ld_out = np.append(ld_out, comp.comp.level_detector(ld_test0))
    for __ in range(b):
        ld_out = np.append(ld_out, comp.comp.level_detector(ld_test1))
    for __ in range(c):
        ld_out = np.append(ld_out, comp.comp.level_detector(ld_test0))
    ld_testx = np.arange(0, (a+b+c)*256)
    fig, ax = plt.subplots()
    ax.plot(ld_testx, ld_out[1:ld_out.shape[0]], linewidth=2.0)
    ax.set(ylim=(-100, 0))
    plt.show()
    
if __name__ == "__main__":
    main()