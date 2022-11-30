#
# Layer for LINE
#

from adafruit_hid.keycode import Keycode

class line:
    color = 0x00ff00
    target = 'LINE'
    btms = None

    def __init__(self, btms):
        self.btms = btms
    
    def toggle_mute(self) -> None:
        print('LINE toggle mute')

    def mute(self) -> None:
        self.toggle_mute()

    def unmute(self) -> None:
        self.toggle_mute()

    def leave(self) -> None:
        print('Leave from LINE')
