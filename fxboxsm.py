import numpy as np
import lcd_screen
import config as cfg

lcd = lcd_screen.lcd_screen("COM6")
m = '@'
moff = 14
voff = 16
class FXBox:
    def __init__(self):
        self.m = self.Menus()
        self.no_states = 0
        self.state = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        self.def_valid_states = np.array([True, True, True, True, True, False, False, False, True, True, False])
        self.valid_states = np.copy(self.def_valid_states)
        self.update_state()
        self.process = True
        
    def new_state(self, new_state):
        if self.state[self.no_states - 1] == 8 or self.state[self.no_states - 1] == 9:
            self.state[self.no_states - 1] = 0
            self.no_states -= 1
        if self.valid_states[new_state] == True:
            if new_state != 0:
                self.state[self.no_states] = new_state
                self.no_states += 1
            else:
                if self.no_states > 0: self.no_states -= 1
                self.state[self.no_states] = 0
        
        print(self.no_states)
        print(self.valid_states)
        print(self.state)
    
    
        # if   self.state[d] == 1:
        #     pass
        # elif self.state[d] == 2:
        #     pass
        # elif self.state[d] == 3:
        #     pass
        # elif self.state[d] == 4:
        #     pass

    def update_state(self):
        self.valid_states = np.copy(self.def_valid_states)
        self.valid_states[8:10] = False
        if self.state[0] == 0:
            self.m.mm()
        elif self.state[0] == 3:
            self.m.p[3].mm()
            self.valid_states[4] = True
            if self.state[1] != 0:
                if self.state[1] == 3 or self.state[1] ==4:
                    self.valid_states[4] = True                
                else:
                    self.valid_states[4] = False
                return self.value_menu(self.m.p[self.state[0]], offset=1), self.state[0:3]
        # compressor menu
        elif self.state[0] != 0:
            if self.state[0] == 4:
                self.valid_states[3:5] = False
            return self.value_menu(self.m), self.state[0:2]
        return None, None
                
    def value_menu(self, mobj, offset=0, ioffset=0):
        mobj.p[self.state[offset + 0]].mm()

        if   self.state[offset + 1] != 0:
            mobj.update_value(0, self.state[offset + 0], self.state[offset + 1])
            self.valid_states[1:5] = False
            self.valid_states[8:10] = True
            if   self.state[offset + 2] == 8:
                return mobj.update_value(-1, self.state[offset + 0], self.state[offset + 1])
            elif self.state[offset + 2] == 9: 
                return mobj.update_value(1, self.state[offset + 0], self.state[offset + 1])
            
    def translator(self, key):
        if   key == '0': # select menu item 1
            state = 0
        elif key == '1':
            state = 1
        elif key == '2': # select menu item 2
            state = 2
        elif key == '3': # select menu item 3
            state = 3
        elif key == '4': # select menu item 4
            state = 4 
        elif key == '-': # -1 to selected value
            state = 8
        elif key == '=': # +1 to selected value
            state = 9
        else:
            state = 10
        return state
            
    
    class Menus:
        def __init__(self):
            self.p = np.empty(5, dtype=object)
            self.p[1] = self.Compressor()
            self.p[2] = self.Convolver()
            self.p[3] = self.Equalizer()
            self.p[4] = self.MasterControls()
        
        def mm(self):
                screen = ["1 Compressor",
                          "2 Convolver",
                          "3 Equalizer",
                          "4 etc."]
                lcd.prints_screen(screen)
                return None
            
        def update_value(self, increment, i1, i2):
            value = self.p[i1].p[i2].update_value(increment)
            self.p[i1].mm()
            lcd.xy_prints(moff, i2, m)
            return value
        
        def update_compressor(self, value, param):
            pass
        class MasterControls:
            def __init__(self):
                self.p = np.empty(5, dtype=object)
                
                self.p[1] = VerticalSlider(-20, 20, cfg.master_pre_gain_db, 1)  # threshold
                self.p[2] = VerticalSlider(-20, 20, cfg.master_post_gain_db, 1) # ratio

            
            def mm(self):
                screen = ["1 Pre Gain",
                          "2 Post Gain",
                          "3 ------",
                          "4 ------"]
                lcd.prints_screen(screen)
                for i in range(1, 3): lcd.xy_prints(voff, i, self.p[i].get_value_str())
                return None
            
        class Convolver:
            def __init__(self):
                self.p = np.empty(5, dtype=object)
                self.p[1] = VerticalSlider(1, 4, cfg.imp_number, 1, decimal_places=0) # imp number
                self.p[2] = VerticalSlider(0, 2, cfg.wet, 0.25, decimal_places=2) # wet
                self.p[3] = VerticalSlider(0, 2, cfg.dry, 0.25, decimal_places=2) # dry
                self.p[4] = VerticalSlider(0, 2, cfg.post, 0.25, decimal_places=2) # post gain
                
            def mm(self):
                screen = ["1 Impulse",
                          "2 Wet Gain",
                          "3 Dry Gain",
                          "4 Post Gain"]
                lcd.prints_screen(screen)
                for i in range(1, 5): lcd.xy_prints(voff, i, str(self.p[i].get_value_str()))
                return None
            
        class Compressor:
            def __init__(self):
                self.p = np.empty(5, dtype=object)
                
                self.p[1] = VerticalSlider(-80, 0, cfg.threshold, 1)  # threshold
                self.p[2] = VerticalSlider(2, 15, cfg.ratio, 1) # ratio
                self.p[3] = VerticalSlider(0.01, 0.5, cfg.attack, 0.01, decimal_places=2) # attack
                self.p[4] = VerticalSlider(0, 20, cfg.post_gain, 1, decimal_places=2) # post gain

            
            def mm(self):
                screen = ["1 Threshold",
                          "2 Ratio",
                          "3 Attack",
                          "4 Post Gain"]
                lcd.prints_screen(screen)
                for i in range(1, 5): lcd.xy_prints(voff, i, self.p[i].get_value_str())
                return None
            
        class Convolver:
            def __init__(self):
                self.p = np.empty(5, dtype=object)
                self.p[1] = VerticalSlider(1, 4, cfg.imp_number, 1, decimal_places=0) # imp number
                self.p[2] = VerticalSlider(0, 2, cfg.wet, 0.25, decimal_places=2) # wet
                self.p[3] = VerticalSlider(0, 2, cfg.dry, 0.25, decimal_places=2) # dry
                self.p[4] = VerticalSlider(0, 2, cfg.post, 0.25, decimal_places=2) # post gain
                
            def mm(self):
                screen = ["1 Impulse",
                          "2 Wet Gain",
                          "3 Dry Gain",
                          "4 Post Gain"]
                lcd.prints_screen(screen)
                for i in range(1, 5): lcd.xy_prints(voff, i, str(self.p[i].get_value_str()))
                return None
            
        class Equalizer:
            def __init__(self):     
                self.p = np.empty(5, dtype=object)
                self.p[1] = self.lp()
                self.p[2] = self.hp()
                self.p[3] = self.bll(i=1)
                self.p[4] = self.bll(i=2)
            def update_value(self, increment, i1, i2):
                value = self.p[i1].p[i2].update_value(increment)
                self.p[i1].mm()
                lcd.xy_prints(moff, i2, m)
                return value
            def mm(self):
                screen = ["1 Lowpass",
                          "2 Highpass",
                          "3 Peaking 1",
                          "4 Peaking 2"]
                lcd.prints_screen(screen)
                return None
            
            class lp:
                def __init__(self):
                    self.p = np.empty(5, dtype=object)
                    self.p[1] = VerticalSlider(0, 1, cfg.lpf_en, 1, decimal_places=0) # enabled
                    self.p[2] = VerticalSlider(5000, 10000, cfg.lpf_fc, 1000, decimal_places=0)# cutoff
                    self.p[3] = VerticalSlider(1, 4, cfg.lpf_N, 1, decimal_places=0) # order
                    
                def mm(self):
                    screen = ["1 LPF On",
                              "2 Cutoff",
                              "3 Order",
                              "4 ------"]
                    lcd.prints_screen(screen)
                    for i in range(1, 4): lcd.xy_prints(voff, i, str(self.p[i].get_value_str()))
                    return None
            
            class hp:
                def __init__(self):
                    self.p = np.empty(5, dtype=object)
                    self.p[1] = VerticalSlider(0, 1, cfg.hpf_en, 1, decimal_places=0) # enabled
                    self.p[2] = VerticalSlider(100, 1000, cfg.hpf_fc, 100, decimal_places=0) # cutoff
                    self.p[3] = VerticalSlider(1, 4, 1, 1, decimal_places=0) # order
                    
                def mm(self):
                    screen = ["1 HPF On",
                              "2 Cutoff",
                              "3 Order",
                              "4 ------"]
                    lcd.prints_screen(screen)
                    for i in range(1, 4): lcd.xy_prints(voff, i, str(self.p[i].get_value_str()))
                    return None
            class bll:
                def __init__(self, i=1):
                    if i==1:
                        en = cfg.bll1_en
                        fgm = cfg.bll1_fgm
                        bfac = cfg.bll1_bfac
                        gdb = cfg.bll1_gdb
                    else:
                        en = cfg.bll2_en
                        fgm = cfg.bll2_fgm
                        bfac = cfg.bll2_bfac
                        gdb = cfg.bll2_gdb
                    self.p = np.empty(5, dtype=object)
                    self.p[1] = VerticalSlider(0, 1, en, 1, decimal_places=1) # enabled
                    self.p[2] = VerticalSlider(100, 15000, fgm, 100, decimal_places=0) # center
                    self.p[3] = VerticalSlider(0.5, 2, bfac, 0.5, decimal_places=1) # bandwith
                    self.p[4] = VerticalSlider(-12, 12, gdb, 1, decimal_places=0)# gain
                
                def mm(self, bp_no=1):
                    screen = ["1 BLL on",
                              "2 Center",
                              "3 Bandwidth",
                              "4 Gain"]
                    lcd.prints_screen(screen)
                    for i in range(1, 5): lcd.xy_prints(voff, i, str(self.p[i].get_value_str()))
                    return None       
    
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
        if self.decimal_places == 0:
            return int(self.value)
        else:
            return self.value
    
    def get_value_str(self):
        return str(round(self.value, self.decimal_places))
    
    def update_slider(self):
        value_rel = self.value_rel
        for j in range(self.height):
            i = self.height - 1 + j
            self.slider[i] = 0
        
def main():
    fxbox = FXBox()
    fxbox.new_state(1)
    fxbox.new_state(1)
    fxbox.new_state(1)
    fxbox.new_state(0)
    
    while True:
        pass
    
if __name__ == "__main__":
    main()