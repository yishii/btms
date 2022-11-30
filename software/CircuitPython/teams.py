#
# Layer for Teams
#

from adafruit_hid.keycode import Keycode

class teams:
    color = 0x0000ff
    target = 'Teams'
    btms = None

    def __init__(self, btms):
        self.btms = btms

    def toggle_mute(self) -> None:
        print('Teams toggle mute')
        self.btms['kbd'].press(Keycode.LEFT_CONTROL)
        self.btms['kbd'].press(Keycode.LEFT_SHIFT)
        self.btms['kbd'].press(Keycode.M)
        self.btms['kbd'].release_all()

    def mute(self) -> None:
        self.toggle_mute()

    def unmute(self) -> None:
        self.toggle_mute()

    def leave(self) -> None:
        print('Leave from TEAMS meeting')
        self.btms['kbd'].press(Keycode.LEFT_CONTROL)
        self.btms['kbd'].press(Keycode.LEFT_SHIFT)
        self.btms['kbd'].press(Keycode.H)
        self.btms['kbd'].release_all()

