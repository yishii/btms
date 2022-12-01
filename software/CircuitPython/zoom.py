#
# Layer for Zoom
# #

from adafruit_hid.keycode import Keycode

class zoom:
    color = 0x00ffff
    target = 'Zoom'
    btms = None

    def __init__(self, btms):
        self.btms = btms
        # btms['kbd'].send(Keycode.A)

    def toggle_mute(self) -> None:
        print('Zoom toggle mute')
        self.btms['kbd'].press(Keycode.LEFT_ALT)
        self.btms['kbd'].press(Keycode.A)
        self.btms['kbd'].release_all()

    def mute(self) -> None:
        self.toggle_mute()

    def unmute(self) -> None:
        self.toggle_mute()

    def leave(self) -> None:
        print('Leave from Zoom meeting')
        self.btms['kbd'].press(Keycode.LEFT_ALT)
        self.btms['kbd'].press(Keycode.V)
        self.btms['kbd'].release_all()
