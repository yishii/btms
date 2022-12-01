#
# Layer for webex
#

from adafruit_hid.keycode import Keycode

class webex:
    color = 0xff0000
    target = 'webex'
    btms = None

    def __init__(self, btms):
        self.btms = btms
    
    def toggle_mute(self) -> None:
        print('webex toggle mute')
        self.btms['kbd'].press(Keycode.LEFT_CONTROL)
        self.btms['kbd'].press(Keycode.M)
        self.btms['kbd'].release_all()

    def mute(self) -> None:
        self.toggle_mute()

    def unmute(self) -> None:
        self.toggle_mute()

    def leave(self) -> None:
        print('Leave from webex meeting')
        self.btms['kbd'].press(Keycode.LEFT_CONTROL)
        self.btms['kbd'].press(Keycode.L)
        self.btms['kbd'].release_all()
