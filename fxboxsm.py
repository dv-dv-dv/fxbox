import lcd_screen
import numpy as np
class FXBox:
    def __init__(self):
        self.lcd = lcd_screen.lcd_screen("COM5")
        self.comp = self.Menus.Compressor()
        self.conv = self.Menus.Convolver()
        self.eq = self.Menus.Equalizer()
        self.mm = self.Menus()
        self.no_states = 0
        self.state = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        self.def_valid_states = np.array([True, True, True, True, True, False, False, False, False, False])
        self.valid_states = np.copy(self.def_valid_states)
        self.marker = "@"
        self.update_state()
        
    def new_state(self, new_state):
        if self.valid_states[new_state] == True:
            if new_state != 0:
                self.state[self.no_states] = new_state
                self.no_states += 1
            else:
                if self.no_states > 0: self.no_states -= 1
                self.state[self.no_states] = 0
            self.update_state()
        
        print(self.valid_states)
        print(self.state)
    
    
    # if self.state[d] == 1:
    #     pass
    # elif self.state[d] == 2:
    #     pass
    # elif self.state[d] == 3:
    #     pass
    # elif self.state[d] == 4:
    #     pass
    # elif self.state[d] != 0:
    #     self.new_state(0)
        
    def update_state(self):
        d = 0
        self.valid_states = np.copy(self.def_valid_states)
        if self.state[d] == 1:
            d = 1
            self.print_screen(self.comp.main_menu())
            self.lcd.pos_prints(15, 1, self.comp.thresh.update_value(0))
            self.lcd.pos_prints(15, 2, self.comp.ratio.update_value(0))
            self.lcd.pos_prints(15, 3, self.comp.atk.update_value(0))
            self.lcd.pos_prints(15, 4, self.comp.post.update_value(0))
            if self.state[d] == 1:
                d = 2
                self.valid_states[8] = self.valid_states[9] = True
                self.lcd.pos_prints(15, 1, self.comp.thresh.update_value(0))
                self.lcd.pos_prints(13, 1, self.marker)
                if self.state[d] == 8:
                    self.lcd.pos_prints(15, 1, self.comp.thresh.update_value(1))
                    self.new_state(0)
                elif self.state[d] == 9:
                    self.lcd.pos_prints(15, 1, self.comp.thresh.update_value(-1))
                    self.new_state(0)
                elif self.state[d] != 0:
                    a = self.state[d]
                    self.new_state(0)
                    if (a > 0) & (a < 5):
                        self.new_state(0)
                        self.new_state(a)
            elif self.state[d] == 2:
                d = 2
                self.valid_states[8] = self.valid_states[9] = True
                self.lcd.pos_prints(15, 2, self.comp.ratio.update_value(0))
                self.lcd.pos_prints(13, 2, self.marker)
                if self.state[d] == 8:
                    self.lcd.pos_prints(15, 2, self.comp.ratio.update_value(1))
                    self.new_state(0)
                elif self.state[d] == 9:
                    self.lcd.pos_prints(15, 2, self.comp.ratio.update_value(-1))
                    self.new_state(0)
                elif self.state[d] != 0:
                    a = self.state[d]
                    self.new_state(0)
                    if (a > 0) & (a < 5):
                        self.new_state(0)
                        self.new_state(a)
            elif self.state[d] == 3:
                d = 2
                self.valid_states[8] = self.valid_states[9] = True
                self.lcd.pos_prints(15, 3, self.comp.atk.update_value(0))
                self.lcd.pos_prints(13, 3, self.marker)
                if self.state[d] == 8:
                    self.lcd.pos_prints(15, 3, self.comp.atk.update_value(1))
                    self.new_state(0)
                elif self.state[d] == 9:
                    self.lcd.pos_prints(15, 3, self.comp.atk.update_value(-1))
                    self.new_state(0)
                elif self.state[d] != 0:
                    a = self.state[d]
                    self.new_state(0)
                    if (a > 0) & (a < 5):
                        self.new_state(0)
                        self.new_state(a)
            elif self.state[d] == 4:
                d = 2
                self.valid_states[8] = self.valid_states[9] = True
                self.lcd.pos_prints(15, 4, self.comp.post.update_value(0))
                self.lcd.pos_prints(13, 4, self.marker)
                if self.state[d] == 8:
                    self.lcd.pos_prints(15, 4, self.comp.post.update_value(1))
                    self.new_state(0)
                elif self.state[d] == 9:
                    self.lcd.pos_prints(15, 4, self.comp.post.update_value(-1))
                    self.new_state(0)
                elif self.state[d] != 0:
                    a = self.state[d]
                    self.new_state(0)
                    if (a > 0) & (a < 5):
                        self.new_state(0)
                        self.new_state(a)
            
        elif self.state[d] == 2:
            d = 1
            self.print_screen(self.conv.main_menu())
            self.lcd.pos_prints(15, 1, self.conv.imp.update_value(0))
            self.lcd.pos_prints(15, 2, self.conv.wet.update_value(0))
            self.lcd.pos_prints(15, 3, self.conv.dry.update_value(0))
            self.lcd.pos_prints(15, 4, self.conv.post.update_value(0))
            if self.state[d] == 1:
                d = 2
                self.valid_states[8] = self.valid_states[9] = True
                self.lcd.pos_prints(15, 1, self.conv.imp.update_value(0))
                self.lcd.pos_prints(13, 1, self.marker)
                if self.state[d] == 8:
                    self.lcd.pos_prints(15, 1, self.conv.imp.update_value(1))
                    self.new_state(0)
                elif self.state[d] == 9:
                    self.lcd.pos_prints(15, 1, self.conv.imp.update_value(-1))
                    self.new_state(0)
                elif self.state[d] != 0:
                    a = self.state[d]
                    self.new_state(0)
                    if (a > 0) & (a < 5):
                        self.new_state(0)
                        self.new_state(a)
            elif self.state[d] == 2:
                d = 2
                self.valid_states[8] = self.valid_states[9] = True
                self.lcd.pos_prints(15, 2, self.conv.wet.update_value(0))
                self.lcd.pos_prints(13, 2, self.marker)
                if self.state[d] == 8:
                    self.lcd.pos_prints(15, 2, self.conv.wet.update_value(1))
                    self.new_state(0)
                elif self.state[d] == 9:
                    self.lcd.pos_prints(15, 2, self.conv.wet.update_value(-1))
                    self.new_state(0)
                elif self.state[d] != 0:
                    a = self.state[d]
                    self.new_state(0)
                    if (a > 0) & (a < 5):
                        self.new_state(0)
                        self.new_state(a)
            elif self.state[d] == 3:
                d = 2
                self.valid_states[8] = self.valid_states[9] = True
                self.lcd.pos_prints(15, 3, self.conv.dry.update_value(0))
                self.lcd.pos_prints(13, 3, self.marker)
                if self.state[d] == 8:
                    self.lcd.pos_prints(15, 3, self.conv.dry.update_value(1))
                    self.new_state(0)
                elif self.state[d] == 9:
                    self.lcd.pos_prints(15, 3, self.conv.dry.update_value(-1))
                    self.new_state(0)
                elif self.state[d] != 0:
                    a = self.state[d]
                    self.new_state(0)
                    if (a > 0) & (a < 5):
                        self.new_state(0)
                        self.new_state(a)
            elif self.state[d] == 4:
                d = 2
                self.valid_states[8] = self.valid_states[9] = True
                self.lcd.pos_prints(15, 4, self.conv.post.update_value(0))
                self.lcd.pos_prints(13, 4, self.marker)
                if self.state[d] == 8:
                    self.lcd.pos_prints(15, 4, self.conv.post.update_value(1))
                    self.new_state(0)
                elif self.state[d] == 9:
                    self.lcd.pos_prints(15, 4, self.conv.post.update_value(-1))
                    self.new_state(0)
                elif self.state[d] != 0:
                    a = self.state[d]
                    self.new_state(0)
                    if (a > 0) & (a < 5):
                        self.new_state(0)
                        self.new_state(a)
                
        elif self.state[d] == 3: 
            d = 1
            self.print_screen(self.eq.main_menu())
            if self.state[d] == 1:
                d = 2
                self.valid_states[4] = False
                self.print_screen(self.eq.lowpass())
                self.lcd.pos_prints(15, 1, self.eq.lpf_enabled.update_value(0))
                self.lcd.pos_prints(15, 2, self.eq.lpf_cutoff.update_value(0))
                self.lcd.pos_prints(15, 3, self.eq.lpf_order.update_value(0))
                if self.state[d] == 1:
                    d = 3
                    self.valid_states[8] = self.valid_states[9] = True
                    self.lcd.pos_prints(15, 1, self.eq.lpf_enabled.update_value(0))
                    self.lcd.pos_prints(13, 1, self.marker)
                    if self.state[d] == 8:
                        self.lcd.pos_prints(15, 1, self.eq.lpf_enabled.update_value(1))
                        self.new_state(0)
                    elif self.state[d] == 9:
                        self.lcd.pos_prints(15, 1, self.eq.lpf_enabled.update_value(-1))
                        self.new_state(0)
                    elif self.state[d] != 0:
                        a = self.state[d]
                        self.new_state(0)
                        if (a > 0) & (a < 5):
                            self.new_state(0)
                            self.new_state(a)
                elif self.state[d] == 2:
                    d = 3
                    self.valid_states[8] = self.valid_states[9] = True
                    self.lcd.pos_prints(15, 2, self.eq.lpf_cutoff.update_value(0))
                    self.lcd.pos_prints(13, 2, self.marker)
                    if self.state[d] == 8:
                        self.lcd.pos_prints(15, 2, self.eq.lpf_cutoff.update_value(1))
                        self.new_state(0)
                    elif self.state[d] == 9:
                        self.lcd.pos_prints(15, 2, self.eq.lpf_cutoff.update_value(-1))
                        self.new_state(0)
                    elif self.state[d] != 0:
                        a = self.state[d]
                        self.new_state(0)
                        if (a > 0) & (a < 5):
                            self.new_state(0)
                            self.new_state(a)
                elif self.state[d] == 3:
                    d = 3
                    self.valid_states[8] = self.valid_states[9] = True
                    self.lcd.pos_prints(15, 3, self.eq.lpf_order.update_value(0))
                    self.lcd.pos_prints(13, 3, self.marker)
                    if self.state[d] == 8:
                        self.lcd.pos_prints(15, 3, self.eq.lpf_order.update_value(1))
                        self.new_state(0)
                    elif self.state[d] == 9:
                        self.lcd.pos_prints(15, 3, self.eq.lpf_order.update_value(-1))
                        self.new_state(0)
                    elif self.state[d] != 0:
                        a = self.state[d]
                        self.new_state(0)
                        if (a > 0) & (a < 5):
                            self.new_state(0)
                            self.new_state(a) 
            elif self.state[d] == 2:
                d = 2
                self.valid_states[4] = False
                self.print_screen(self.eq.highpass())
                self.lcd.pos_prints(15, 1, self.eq.hpf_enabled.update_value(0))
                self.lcd.pos_prints(15, 2, self.eq.hpf_cutoff.update_value(0))
                self.lcd.pos_prints(15, 3, self.eq.hpf_order.update_value(0))
                if self.state[d] == 1:
                    d = 3
                    self.valid_states[8] = self.valid_states[9] = True
                    self.lcd.pos_prints(15, 1, self.eq.hpf_enabled.update_value(0))
                    self.lcd.pos_prints(13, 1, self.marker)
                    if self.state[d] == 8:
                        self.lcd.pos_prints(15, 1, self.eq.hpf_enabled.update_value(1))
                        self.new_state(0)
                    elif self.state[d] == 9:
                        self.lcd.pos_prints(15, 1, self.eq.hpf_enabled.update_value(-1))
                        self.new_state(0)
                    elif self.state[d] != 0:
                        a = self.state[d]
                        self.new_state(0)
                        if (a > 0) & (a < 5):
                            self.new_state(0)
                            self.new_state(a)
                elif self.state[d] == 2:
                    d = 3
                    self.valid_states[8] = self.valid_states[9] = True
                    self.lcd.pos_prints(15, 2, self.eq.hpf_cutoff.update_value(0))
                    self.lcd.pos_prints(13, 2, self.marker)
                    if self.state[d] == 8:
                        self.lcd.pos_prints(15, 2, self.eq.hpf_cutoff.update_value(1))
                        self.new_state(0)
                    elif self.state[d] == 9:
                        self.lcd.pos_prints(15, 2, self.eq.hpf_cutoff.update_value(-1))
                        self.new_state(0)
                    elif self.state[d] != 0:
                        a = self.state[d]
                        self.new_state(0)
                        if (a > 0) & (a < 5):
                            self.new_state(0)
                            self.new_state(a)
                elif self.state[d] == 3:
                    d = 3
                    self.valid_states[8] = self.valid_states[9] = True
                    self.lcd.pos_prints(15, 3, self.eq.hpf_order.update_value(0))
                    self.lcd.pos_prints(13, 3, self.marker)
                    if self.state[d] == 8:
                        self.lcd.pos_prints(15, 3, self.eq.hpf_order.update_value(1))
                        self.new_state(0)
                    elif self.state[d] == 9:
                        self.lcd.pos_prints(15, 3, self.eq.hpf_order.update_value(-1))
                        self.new_state(0)
                    elif self.state[d] != 0:
                        a = self.state[d]
                        self.new_state(0)
                        if (a > 0) & (a < 5):
                            self.new_state(0)
            elif self.state[d] == 3:
                d = 2
                self.print_screen(self.eq.bandpass())
                self.lcd.pos_prints(15, 1, self.eq.bpf1_gain.update_value(0))
                self.lcd.pos_prints(15, 2, self.eq.bpf1_center.update_value(0))
                self.lcd.pos_prints(15, 3, self.eq.bpf1_bandw.update_value(0))
                self.lcd.pos_prints(15, 4, self.eq.bpf1_order.update_value(0))
                if self.state[d] == 1:
                    d = 3
                    self.valid_states[8] = self.valid_states[9] = True
                    self.lcd.pos_prints(15, 1, self.eq.bpf1_gain.update_value(0))
                    self.lcd.pos_prints(13, 1, self.marker)
                    if self.state[d] == 8:
                        self.lcd.pos_prints(15, 1, self.eq.bpf1_gain.update_value(1))
                        self.new_state(0)
                    elif self.state[d] == 9:
                        self.lcd.pos_prints(15, 1, self.eq.bpf1_gain.update_value(-1))
                        self.new_state(0)
                    elif self.state[d] != 0:
                        a = self.state[d]
                        self.new_state(0)
                        if (a > 0) & (a < 5):
                            self.new_state(0)
                            self.new_state(a)
                elif self.state[d] == 2:
                    d = 3
                    self.valid_states[8] = self.valid_states[9] = True
                    self.lcd.pos_prints(15, 2, self.eq.bpf1_center.update_value(0))
                    self.lcd.pos_prints(13, 2, self.marker)
                    if self.state[d] == 8:
                        self.lcd.pos_prints(15, 2, self.eq.bpf1_center.update_value(1))
                        self.new_state(0)
                    elif self.state[d] == 9:
                        self.lcd.pos_prints(15, 2, self.eq.bpf1_center.update_value(-1))
                        self.new_state(0)
                    elif self.state[d] != 0:
                        a = self.state[d]
                        self.new_state(0)
                        if (a > 0) & (a < 5):
                            self.new_state(0)
                            self.new_state(a)
                elif self.state[d] == 3:
                    d = 3
                    self.valid_states[8] = self.valid_states[9] = True
                    self.lcd.pos_prints(15, 3, self.eq.bpf1_bandw.update_value(0))
                    self.lcd.pos_prints(13, 3, self.marker)
                    if self.state[d] == 8:
                        self.lcd.pos_prints(15, 3, self.eq.bpf1_bandw.update_value(1))
                        self.new_state(0)
                    elif self.state[d] == 9:
                        self.lcd.pos_prints(15, 3, self.eq.bpf1_bandw.update_value(-1))
                        self.new_state(0)
                    elif self.state[d] != 0:
                        a = self.state[d]
                        self.new_state(0)
                        if (a > 0) & (a < 5):
                            self.new_state(0)
                            self.new_state(a)
                elif self.state[d] == 4:
                    d = 3
                    self.valid_states[8] = self.valid_states[9] = True
                    self.lcd.pos_prints(15, 4, self.eq.bpf1_order.update_value(0))
                    self.lcd.pos_prints(13, 4, self.marker)
                    if self.state[d] == 8:
                        self.lcd.pos_prints(15, 4, self.eq.bpf1_order.update_value(1))
                        self.new_state(0)
                    elif self.state[d] == 9:
                        self.lcd.pos_prints(15, 4, self.eq.bpf1_order.update_value(-1))
                        self.new_state(0)
                    elif self.state[d] != 0:
                        a = self.state[d]
                        self.new_state(0)
                        if (a > 0) & (a < 5):
                            self.new_state(0)
                            self.new_state(a)
            elif self.state[d] == 4:
                d = 2
                self.print_screen(self.eq.bandpass(bp_no=2))
                self.lcd.pos_prints(15, 1, self.eq.bpf2_gain.update_value(0))
                self.lcd.pos_prints(15, 2, self.eq.bpf2_center.update_value(0))
                self.lcd.pos_prints(15, 3, self.eq.bpf2_bandw.update_value(0))
                self.lcd.pos_prints(15, 4, self.eq.bpf2_order.update_value(0))
                if self.state[d] == 1:
                    d = 3
                    self.valid_states[8] = self.valid_states[9] = True
                    self.lcd.pos_prints(15, 1, self.eq.bpf2_gain.update_value(0))
                    self.lcd.pos_prints(13, 1, self.marker)
                    if self.state[d] == 8:
                        self.lcd.pos_prints(15, 1, self.eq.bpf2_gain.update_value(1))
                        self.new_state(0)
                    elif self.state[d] == 9:
                        self.lcd.pos_prints(15, 1, self.eq.bpf2_gain.update_value(-1))
                        self.new_state(0)
                    elif self.state[d] != 0:
                        a = self.state[d]
                        self.new_state(0)
                        if (a > 0) & (a < 5):
                            self.new_state(0)
                            self.new_state(a)
                elif self.state[d] == 2:
                    d = 3
                    self.valid_states[8] = self.valid_states[9] = True
                    self.lcd.pos_prints(15, 2, self.eq.bpf2_center.update_value(0))
                    self.lcd.pos_prints(13, 2, self.marker)
                    if self.state[d] == 8:
                        self.lcd.pos_prints(15, 2, self.eq.bpf2_center.update_value(1))
                        self.new_state(0)
                    elif self.state[d] == 9:
                        self.lcd.pos_prints(15, 2, self.eq.bpf2_center.update_value(-1))
                        self.new_state(0)
                    elif self.state[d] != 0:
                        a = self.state[d]
                        self.new_state(0)
                        if (a > 0) & (a < 5):
                            self.new_state(0)
                            self.new_state(a)
                elif self.state[d] == 3:
                    d = 3
                    self.valid_states[8] = self.valid_states[9] = True
                    self.lcd.pos_prints(15, 3, self.eq.bpf2_bandw.update_value(0))
                    self.lcd.pos_prints(13, 3, self.marker)
                    if self.state[d] == 8:
                        self.lcd.pos_prints(15, 3, self.eq.bpf2_bandw.update_value(1))
                        self.new_state(0)
                    elif self.state[d] == 9:
                        self.lcd.pos_prints(15, 3, self.eq.bpf2_bandw.update_value(-1))
                        self.new_state(0)
                    elif self.state[d] != 0:
                        a = self.state[d]
                        self.new_state(0)
                        if (a > 0) & (a < 5):
                            self.new_state(0)
                            self.new_state(a)
                elif self.state[d] == 4:
                    d = 3
                    self.valid_states[8] = self.valid_states[9] = True
                    self.lcd.pos_prints(15, 4, self.eq.bpf2_order.update_value(0))
                    self.lcd.pos_prints(13, 4, self.marker)
                    if self.state[d] == 8:
                        self.lcd.pos_prints(15, 4, self.eq.bpf2_order.update_value(1))
                        self.new_state(0)
                    elif self.state[d] == 9:
                        self.lcd.pos_prints(15, 4, self.eq.bpf2_order.update_value(-1))
                        self.new_state(0)
                    elif self.state[d] != 0:
                        a = self.state[d]
                        self.new_state(0)
                        if (a > 0) & (a < 5):
                            self.new_state(0)
                            self.new_state(a)
                
        elif self.state[d] == 4:
            self.new_state(0)
                
                
        else:
            self.print_screen(self.mm.main_menu())
            
    def translator(self, key):
        if key == '1':
            state = 1
        elif key == '2':
            state = 2
        elif key == '3':
            state = 3
        elif key == '4':
            state = 4
        elif key == '-':
            state = 9
        elif key == '=':
            state = 8
        else:
            state = 0
        return state
    
    def print_screen(self, screen):
        self.lcd.clear()
        for i in range(len(screen)):
            self.lcd.pos_prints(1, i + 1, screen[i])
            
    
    class Menus:
        def main_menu(self):
                screen = ["1 Compressor",
                          "2 Convolver",
                          "3 Equalizer",
                          "4 ------"]
                return screen
        class Compressor:
            def __init__(self):
                self.thresh = VerticalSlider(-80, 0, -15, -1)
                self.ratio = VerticalSlider(1, 10, 4, 0.5)
                self.atk = VerticalSlider(0.005, 0.5, 0.01, 0.005, decimal_places=3)
                self.post = VerticalSlider(0.005, 1, 0.5, 0.005, decimal_places=3)
                
            def main_menu(self):
                screen = ["1 Threshold",
                          "2 Ratio",
                          "3 Attack",
                          "4 Post Gain"]
                return screen
            
            def get_values(self):
                return self.thresh.get_value(), self.ration.get_value(), self.atk.get_value(), self.post.get_value()
            
        class Convolver:
            def __init__(self):
                self.imp = VerticalSlider(1, 4, 0, 1, decimal_places=0)
                self.wet = VerticalSlider(-12, 12, 0, 0.5, decimal_places=1)
                self.dry = VerticalSlider(-12, 12, 0, 0.5, decimal_places=1)
                self.post = VerticalSlider(-12, 12, 0, 0.5, decimal_places=1)
                
            def main_menu(self):
                screen = ["1 Impulse",
                          "2 Wet Gain",
                          "3 Dry Gain",
                          "4 Post Gain"]
                return screen
            def get_values(self):
                return self.imp.get_value(), self.wet.get_value(), self.dry.get_value(), self.post.get_value()
                
        class Equalizer:
            def __init__(self):
                self.lpf_enabled = VerticalSlider(0, 1, 0, 1, decimal_places=0)
                self.lpf_cutoff = VerticalSlider(1000, 10000, 5000, 1000, decimal_places=0)
                self.lpf_order = VerticalSlider(1, 4, 1, 1, decimal_places=0)
                
                self.hpf_enabled = VerticalSlider(0, 1, 0, 1, decimal_places=0)
                self.hpf_cutoff = VerticalSlider(100, 1000, 100, 100, decimal_places=0)
                self.hpf_order = VerticalSlider(1, 4, 1, 1, decimal_places=0)
                
                self.bpf1_gain = VerticalSlider(-12, 12, 0, 0.5, decimal_places=1)
                self.bpf1_center = VerticalSlider(100, 15000, 1000, 100, decimal_places=0)
                self.bpf1_bandw = VerticalSlider(10, 100, 50, 10, decimal_places=0)
                self.bpf1_order = VerticalSlider(1, 4, 1, 1, decimal_places=0)             
                
                self.bpf2_gain = VerticalSlider(-12, 12, 0, 0.5, decimal_places=1)
                self.bpf2_center = VerticalSlider(100, 15000, 1000, 100, decimal_places=0)
                self.bpf2_bandw = VerticalSlider(10, 100, 50, 10, decimal_places=0)
                self.bpf2_order = VerticalSlider(1, 4, 1, 1, decimal_places=0)         
                
            def get_lpf_values(self):
                return self.lpf_enabled.get_value(), self.lpf_cutoff.get_value(), self.lpf_order.get_value()
            
            def get_hpf_values(self):
                return self.hpf_enabled.get_value(), self.hpf_cutoff.get_value(), self.hpf_order.get_value()
            
            def get_bpf1_values(self):
                return self.bpf1_gain.get_value(), self.bpf1_center.get_value(), self.bpf1_bandw.get_value(), self.bpf1_order.get_value()
            
            def get_bpf2_values(self):
                return self.bpf2_gain.get_value(), self.bpf2_center.get_value(), self.bpf2_bandw.get_value(), self.bpf2_order.get_value()
            
            def main_menu(self):
                screen = ["1 Lowpass",
                          "2 Highpass",
                          "3 Peaking 1",
                          "4 Peaking 2"]
                return screen
            
            def lowpass(self):
                screen = ["1 LPF On",
                          "2 Cutoff",
                          "3 Order",
                          "4 ------"]
                return screen
            
            def highpass(self):
                screen = ["1 HPF On",
                          "2 Cutoff",
                          "3 Order",
                          "4 ------"]
                return screen
            def bandpass(self, bp_no=1):
                screen = ["1 Gain",
                          "2 Center",
                          "3 Bandwidth",
                          "4 Order"]
                return screen                
    
class VerticalSlider:
    def __init__(self, min_value, max_value, initial_value, step_by, height=3, subheight=8, decimal_places=2):
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.step_by = step_by
        self.vrc = subheight*height/(max_value - min_value)
        self.value_rel = initial_value
        self.height = height
        self.subheight = height
        self.decimal_places = decimal_places
        self.slider = []
        for i in range(height):
            self.slider.append(0)
        
    def update_value(self, change_by, mult=1):
        self.value += change_by*mult*self.step_by
        if self.value > self.max_value: 
            self.value = self.max_value
        elif self.value < self.min_value: 
            self.value = self.min_value
        return str(round(self.value, self.decimal_places))
    
    def get_value(self):
        return self.value
    
    def update_slider(self):
        value_rel = self.value_rel
        for j in range(self.height):
            i = self.height - 1 + j
            self.slider[i] = 0
        
def main():
    fxbox = FXBoxStateMachine()
    fxbox.new_state(1)
    fxbox.new_state(1)
    fxbox.new_state(1)
    fxbox.new_state(0)
    
    while True:
        pass
    
if __name__ == "__main__":
    main()