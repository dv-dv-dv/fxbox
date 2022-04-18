import serial
class lcd_screen:

            
    def __init__(self, serial_port, columns=20, rows=4):
        self.ser = serial.Serial(serial_port, 9600, timeout=1)
        self.vertical_bars()
        self.set_size(20, 4)
        self.set_color(255, 5, 5)
        self.set_brightness(255)
        self.set_contrast(255)
        self.set_autoscroll(False)
        self.set_block(False)
        self.set_underline(False)
        self.reset_pos()
        self.clear()
        self.set_on(True)
        
    def close(self):
        self.clear()
        self.set_on(False)
        self.ser.close()
        
    def hex_command_matrix(self, hex_matrix):
        self.ser.write(chr(0xFE).encode("latin-1"))
        for hex_command in hex_matrix:
            self.ser.write(chr(hex_command).encode("latin-1"))
            
    def set_size(self, columns, rows):
        self.ser.write(chr(0xFE).encode("latin-1"))
        self.ser.write(chr(columns).encode("latin-1"))
        self.ser.write(chr(rows).encode("latin-1"))
        self.columns = columns
        self.rows = rows
        
    def set_color(self, red, green, blue):
        hex_matrix = [0xFE, 0xD0, red, green, blue]
        for hex_command in hex_matrix:
            self.ser.write(chr(hex_command).encode("latin-1"))
        self.red = red
        self.green = green
        self.blue = blue
            
    def set_brightness(self, brightness):
        self.ser.write(chr(0xFE).encode("latin-1"))
        self.ser.write(chr(0x99).encode("latin-1"))
        self.ser.write(chr(brightness).encode("latin-1"))
        self.brightness = brightness
        
    def set_contrast(self, contrast):
        self.ser.write(chr(0xFE).encode("latin-1"))
        self.ser.write(chr(0x50).encode("latin-1"))
        self.ser.write(chr(contrast).encode("latin-1"))
        self.contrast = contrast
        
    def set_startup_screen(self, text):       
        self.ser.write(chr(0xFE).encode("latin-1"))
        self.ser.write(chr(0x40).encode("latin-1"))
        self.print_text(text)
        
    def prints(self, text):
        self.ser.write(text.encode())
        self.update_pos(self.x + len(text), self.y)
        
    def prints_xy(self, text, x, y):
        self.set_pos(x, y)
        self.prints(text)
    
    def prints_screen(self, screen):
        self.clear()
        for i in range(len(screen)):
            self.xy_prints(1, i + 1, screen[i])
    
    def x_prints_screen(self, screen, x):
        self.clear()
        for i in range(len(screen)):
            self.xy_prints(x, i + 1, screen[i])
        
    def xy_prints(self, x, y, text):
        self.set_pos(x, y)
        self.prints(text)
        
    def clear(self):
        self.ser.write(chr(0xFE).encode("latin-1"))
        self.ser.write(chr(0x58).encode("latin-1"))
        self.set_pos(1, 1)
    
    def set_on(self, on):
        self.ser.write(chr(0xFE).encode("latin-1"))
        if on==True:
            self.ser.write(chr(0x42).encode("latin-1"))
            self.ser.write(chr(0x00).encode("latin-1"))
        else:
            self.ser.write(chr(0x46).encode("latin-1"))
        self.on = on
            
    def set_autoscroll(self, autoscroll):        
        self.ser.write(chr(0xFE).encode("latin-1"))
        if autoscroll==True:
            self.ser.write(chr(0x51).encode("latin-1"))
        else:
            self.ser.write(chr(0x51).encode("latin-1"))
        self.autoscroll = autoscroll
            
    def set_pos(self, x, y):
        self.update_pos(x, y)
        self.ser.write(chr(0xFE).encode("latin-1"))
        self.ser.write(chr(0x47).encode("latin-1"))
        self.ser.write(chr(self.x).encode("latin-1"))
        self.ser.write(chr(self.y).encode("latin-1"))
        
    def forward(self):
        self.ser.write(chr(0xFE).encode("latin-1"))
        self.ser.write(chr(0x4D).encode("latin-1"))
        self.update_pos(self.x + 1, 1)
        
    def back(self):
        self.ser.write(chr(0xFE).encode("latin-1"))
        self.ser.write(chr(0x4C).encode("latin-1"))
        self.update_pos(self.x - 1, 1)
        
    def reset_pos(self):
        self.ser.write(chr(0xFE).encode("latin-1"))
        self.ser.write(chr(0x48).encode("latin-1"))
        self.update_pos(1, 1)
        
    def update_pos(self, x, y):
        while x > self.columns: 
            x -= self.columns
            y += 1
        while x < 1: 
            x += self.columns
            y -= 1
        while y > self.rows: 
            y -= self.rows
        while y < 1: 
            y += self.rows
        self.x = x
        self.y = y
        
    def set_block(self, cursor_block):
        self.ser.write(chr(0xFE).encode("latin-1"))
        if cursor_block == True:
            self.ser.write(chr(0x53).encode("latin-1"))
        else:
            self.ser.write(chr(0x54).encode("latin-1"))
        self.cursor_block = cursor_block
            
    def set_underline(self, cursor_underline):
        self.ser.write(chr(0xFE).encode("latin-1"))
        if cursor_underline == True:
            self.ser.write(chr(0x4A).encode("latin-1"))
        else:
            self.ser.write(chr(0x4B).encode("latin-1"))
        self.cursor_underline = cursor_underline
    
    def create_custom_char(self, char_no, char):
        if len(char)==8:
            self.ser.write(chr(0xFE).encode("latin-1"))
            self.ser.write(chr(0x4E).encode("latin-1"))
            self.ser.write(chr(char_no).encode("latin-1"))
            for x in char:
                self.ser.write(chr(x).encode("latin-1"))
                
    def print_custom_char(self, char_no):
        self.ser.write(chr(char_no).encode("latin-1"))
    
    def art_to_custom_char(self, art):
        width = len(art[0])
        height = len(art)
        if (width==5)&(height==8):
            pass
    
    def vertical_bars(self):
        self.create_custom_char(0, [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1F])
        self.create_custom_char(1, [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1F, 0x1F])
        self.create_custom_char(2, [0x00, 0x00, 0x00, 0x00, 0x00, 0x1F, 0x1F, 0x1F])
        self.create_custom_char(3, [0x00, 0x00, 0x00, 0x00, 0x1F, 0x1F, 0x1F, 0x1F])
        self.create_custom_char(4, [0x00, 0x00, 0x00, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F])
        self.create_custom_char(5, [0x00, 0x00, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F])
        self.create_custom_char(6, [0x00, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F])
        self.create_custom_char(7, [0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F])
        
def main():
    lcd = lcd_screen("COM5")
    lcd.close()
    
if __name__ == "__main__":
    main()