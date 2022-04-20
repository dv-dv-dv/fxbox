import pynput.keyboard
import fxboxsm
def on_press(key):
    try:
        state = fxbox.translator(key.char)
        fxbox.new_state(state)
        print(str(fxbox.update_state()))
    except AttributeError:
        pass

def on_release(key):
    pass
fxbox = fxboxsm.FXBox()
# Collect events until released
with pynput.keyboard.Listener(
        on_press=on_press,
        on_release=on_release) as listener:
    listener.join()

#..or, in a non-blocking fashion:1099091110909=-=-111=-=-1=-=-10000
listener = pynput.keyboard.Listener(
    on_press=on_press,
    on_release=on_release)
listener.start()