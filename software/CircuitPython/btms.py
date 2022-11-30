#
# BTMS for CircuitPython
#
# with Seeeduino Xiao RP2040, use this below;
#  https://circuitpython.org/board/seeeduino_xiao_rp2040/

from board import *
import rotaryio
import digitalio
import time
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from neopixel import *
import busio
import usb_cdc
import re
import layers_conf

PIN_A = D7
PIN_B = D8
# PIN_CENTER_PUSH = D2 # for Xiao(SAMD)
PIN_CENTER_PUSH = D0   # for Xiao(RP2040)
# PIN_NEOPIXEL = D6    # for Xiao(SAMD)
PIN_NEOPIXEL = D10     # for Xiao(RP2040)
PIN_TACTILE_SW = D3

PIN_I2C_SCL = D5
PIN_I2C_SDA = D4

I2C_SLAVE_ADDRESS_6BUTTON_KEYDOCK = 0x48

LED_INDICATOR_CHANGE_ONLINE_APPLICATION = 1
LED_INDICATOR_TOGGLE_MUTE_MODE = 2
LED_INDICATOR_SHOW_CURRENT_ONLINE_APPLICATION = 3
LED_INDICATOR_OFF = 100

DOCK_NONE = 0
DOCK_6KEYS = 1

MODE_NORMAL = 0
MODE_WINDOW_CHANGE = 1
MODE_CHANGE_ONLINE_APPLICATION = 2

current_mode = MODE_NORMAL

host_managed_mode = False
btms = {}

class Button:
    gpio = None
    checked_time_last = 1
    pushed_time = 0
    pushed_value_last = True
    on_press_short = None
    on_press_long = None
    after_long_pressed_and_still_pressed = False

    def __init__(self, gpio, on_press_short, on_press_long = None):
        self.gpio = gpio
        self.on_press_short = on_press_short
        self.on_press_long = on_press_long
    
    def poll(self):
        current_time = time.monotonic()
        if current_time > (self.checked_time_last + 0.1):
            self.checked_time_last = current_time
            gpio_value = self.gpio.value
            if (gpio_value == False):
                if self.after_long_pressed_and_still_pressed:
                    return
                self.pushed_time = self.pushed_time + 1
                if (self.pushed_time > 4):
                    if self.on_press_long is not None:
                        self.on_press_long()
                        self.after_long_pressed_and_still_pressed = True
            elif (gpio_value == True) and (self.pushed_value_last == False):
                if self.after_long_pressed_and_still_pressed:
                    self.after_long_pressed_and_still_pressed = False
                else:
                    self.on_press_short()
                self.pushed_time = 0
            self.pushed_value_last = gpio_value

class Layer:
    active_layer_no = 0
    max_application_type = 0
    layers = []
    active_layer = None

    def __init__(self):
        for layer in layers_conf.layers:
            m = __import__(layer)
            m_class = getattr(m, layer)
            m_instance = m_class(btms)
            self.layers += [m_instance]
            self.max_application_type += 1
            print(f'imported module {layer} [{m_instance.target}]')
        self.active_layer = self.layers[self.active_layer_no]

    def get_color(self):
        return self.active_layer.color
    
    def get_target(self):
        return self.active_layer.target
    
    def set_next(self):
        self.active_layer_no = (self.active_layer_no + 1) % self.max_application_type
        self.active_layer = self.layers[self.active_layer_no]
        print(f'Layer changed to {self.active_layer.target}')

    def set_prev(self):
        self.active_layer_no = (self.active_layer_no - 1) % self.max_application_type
        self.active_layer = self.layers[self.active_layer_no]
        print(f'Layer changed to {self.active_layer.target}')

    def mute(self):
        self.active_layer.mute()
    
    def unmute(self):
        self.active_layer.unmute()
    
    def leave(self):
        self.active_layer.leave()

def on_rotate(cw):
    global current_mode, blink_color
    if (current_mode == MODE_NORMAL):
        current_mode = MODE_WINDOW_CHANGE
        kbd.press(Keycode.LEFT_ALT);
    elif (current_mode == MODE_WINDOW_CHANGE):
        pass
    elif (current_mode == MODE_CHANGE_ONLINE_APPLICATION):
        pass

    if current_mode == MODE_WINDOW_CHANGE:
        print('rotate')
        if cw:
            kbd.press(Keycode.SHIFT, Keycode.TAB)
            kbd.release(Keycode.SHIFT, Keycode.TAB)
        else:
            kbd.press(Keycode.TAB)
            kbd.release(Keycode.TAB)
    elif current_mode == MODE_CHANGE_ONLINE_APPLICATION:
        if cw:
            layers.set_next()
            blink_color = layers.get_color()
        else:
            layers.set_prev()
            blink_color = layers.get_color()

rotate_state = 0
last_position = None
def manage_knob():
    global rotate_state
    global last_position
    position = encoder.position # エンコーダーカウント値取得
    if last_position is None:
        last_position = position
    if position != last_position:
        if(position < last_position):
            on_rotate(True)
        elif(position > last_position):
            on_rotate(False)
    last_position = position

internal_mute_state = False
def switch_mute_state():
    global internal_mute_state
    if internal_mute_state is True:
        layers.mute()
    else:
        layers.unmute()
    internal_mute_state = True if not internal_mute_state else False
    led_indicate(LED_INDICATOR_TOGGLE_MUTE_MODE)

current_led_color = None
saved_led_color = None
def set_led_color(color):
    global current_led_color
    led[0] = color
    led.show()
    current_led_color = led[0]

def save_led_color():
    global current_led_color
    global saved_led_color
    saved_led_color = current_led_color

def restore_led_color():
    global saved_led_color
    set_led_color(saved_led_color)

led_mode = LED_INDICATOR_OFF
mute_state = False
blink_interval = 1
start_time = 0
blink_state = False
enable_blink = False
blink_color = None

def led_indicate(mode):
    global mute_state, enable_blink, blink_color, blink_interval

    if mode == LED_INDICATOR_CHANGE_ONLINE_APPLICATION:
        blink_interval = 0.1
        blink_color = layers.get_color()
        enable_blink = True
    else:
        enable_blink = False

    if mode == LED_INDICATOR_TOGGLE_MUTE_MODE:
        if mute_state:
            set_led_color((255, 255, 0))
        else:
            set_led_color((255, 100, 0))
        mute_state = False if mute_state else True
    elif mode == LED_INDICATOR_SHOW_CURRENT_ONLINE_APPLICATION:
        save_led_color()
        for _ in range(2):
            set_led_color(layers.get_color())
            time.sleep(0.5)
            set_led_color((0, 0, 0))
            time.sleep(0.5)
        restore_led_color()
    elif mode == LED_INDICATOR_OFF:
        set_led_color((0, 0, 0))

def manage_led():
    global start_time, blink_interval, blink_state, enable_blink, blink_color
    if enable_blink:
        if time.monotonic() > (start_time + blink_interval):
            start_time = time.monotonic()
            if blink_state:
                led[0] = blink_color
            else:
                led[0] = (0, 0, 0)
            led.show()
            blink_state = not blink_state

def on_center_short_press():
    global current_mode
    if current_mode == MODE_NORMAL:
        if host_managed_mode:
            # print('center_short_press')
            usb_cdc.console.write(b'center_short_press\r\n')
        else:
            switch_mute_state()
    elif current_mode == MODE_CHANGE_ONLINE_APPLICATION:
        led_indicate(LED_INDICATOR_SHOW_CURRENT_ONLINE_APPLICATION)
        current_mode = MODE_NORMAL
    elif current_mode == MODE_WINDOW_CHANGE:
        kbd.release(Keycode.LEFT_ALT);
        if host_managed_mode is not True:
            switch_mute_state()
        current_mode = MODE_NORMAL

def on_center_long_press():
    global current_mode
    print('4')
    if current_mode == MODE_NORMAL:
        layers.leave()


def on_side_short_press():
    global current_mode
    print('2')
    if current_mode == MODE_NORMAL:
        led_indicate(LED_INDICATOR_SHOW_CURRENT_ONLINE_APPLICATION)

def on_side_long_press():
    global current_mode
    print('3')
    if current_mode == MODE_NORMAL:
        current_mode = MODE_CHANGE_ONLINE_APPLICATION
        save_led_color()
        led_indicate(LED_INDICATOR_CHANGE_ONLINE_APPLICATION)

def on_attach_dock(dock_type):
    print('New dock :' + str(dock_type))
    if dock_type == DOCK_6KEYS:
        print('Initialize for 6KEYS DOCK')
        dock6keys.initialize()

attached_dock_type = DOCK_NONE
last_checked_dock_time = 0

def manage_dock():
    global last_checked_dock_time, attached_dock_type
    if (time.monotonic() > last_checked_dock_time + 1):
        try:
            detected_slave_address = i2c.scan().pop()
            if(detected_slave_address == I2C_SLAVE_ADDRESS_6BUTTON_KEYDOCK):
                detected_dock = DOCK_6KEYS
            else:
                detected_dock = DOCK_NONE
            if(detected_dock != attached_dock_type):
                attached_dock_type = detected_dock
                on_attach_dock(attached_dock_type)
            last_checked_dock_time = time.monotonic()
        except IndexError:
            detected_dock = DOCK_NONE

class Dock6Keys:
    on_key_press = None
    last_pressed = 0x00

    def __init__(self, key1, key2, key3, key4, key5, key6):
        self.on_key_press = []
        self.on_key_press += [key1]
        self.on_key_press += [key2]
        self.on_key_press += [key3]
        self.on_key_press += [key4]
        self.on_key_press += [key5]
        self.on_key_press += [key6]

    def initialize(self):
        for led in range(6):
            self.set_led(led, (0, 0, 0))
    
    def set_led(self, led_no, rgb):
        if(led_no < 6):
            i2c.writeto(I2C_SLAVE_ADDRESS_6BUTTON_KEYDOCK, bytes([led_no, rgb[0], rgb[1], rgb[2]]))
    
    def poll(self):
        receive_data = bytearray(1)
        i2c.readfrom_into(I2C_SLAVE_ADDRESS_6BUTTON_KEYDOCK, receive_data)
        pressed = receive_data[0]
        pressed_differs = pressed ^ self.last_pressed
        for key in range(6):
            mask_bit = 1 << key
            if(pressed_differs & mask_bit):
                if (pressed & mask_bit == mask_bit):
                    self.on_key_press[key](True)
                else:
                    self.on_key_press[key](False)
        self.last_pressed = pressed

fn_pressed = False
def on_dock6_key1_press(pressed):
    if pressed:
        dock6keys.set_led(0, (255, 255, 255))
        if fn_pressed:
            kbd.send(Keycode.A)
        else:
            kbd.send(Keycode.F)
    else:
        dock6keys.set_led(0, (0, 0, 0))

def on_dock6_key2_press(pressed):
    if pressed:
        dock6keys.set_led(1, (255, 255, 255))
        if fn_pressed:
            kbd.send(Keycode.B)
        else:
            kbd.send(Keycode.G)
    else:
        dock6keys.set_led(1, (0, 0, 0))

def on_dock6_key3_press(pressed):
    if pressed:
        dock6keys.set_led(2, (255, 255, 255))
        if fn_pressed:
            kbd.send(Keycode.C)
        else:
            kbd.send(Keycode.H)
    else:
        dock6keys.set_led(2, (0, 0, 0))

def on_dock6_key4_press(pressed):
    if pressed:
        dock6keys.set_led(3, (255, 255, 255))
        if fn_pressed:
            kbd.send(Keycode.D)
        else:
            kbd.send(Keycode.I)
    else:
        dock6keys.set_led(3, (0, 0, 0))

def on_dock6_key5_press(pressed):
    if pressed:
        dock6keys.set_led(4, (255, 255, 255))
        fn_pressed = True
    else:
        dock6keys.set_led(4, (0, 0, 0))
        fn_pressed = False

def on_dock6_key6_press(pressed):
    if pressed:
        dock6keys.set_led(5, (255, 255, 255))
        if fn_pressed:
            kbd.send(Keycode.E)
        else:
            kbd.send(Keycode.J)
    else:
        dock6keys.set_led(5, (0, 0, 0))

re_led = re.compile(r'led ([0-9]*) ([0-9]*) ([0-9]*)')

def command_input():
    global host_managed_mode

    if(usb_cdc.console.in_waiting == 0):
        return

    line = usb_cdc.console.readline()
    line = line.decode().replace('\n', '')

    if(line == 'host_manage'):
        host_managed_mode = True
        print('Entered to host-managed mode')
    elif(line == 'device_manage'):
        host_managed_mode = False
        print('Leave from host-managed mode')
    else:
        if host_managed_mode:
            match = re_led.match(line)
            if match:
                color = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
                # print(f'{int(match.group(1))}, {int(match.group(2))}, {int(match.group(3))}')
                set_led_color(color)

if __name__ == "__main__":
    i2c = busio.I2C(PIN_I2C_SCL, PIN_I2C_SDA, frequency=100000)

    while not i2c.try_lock():
        pass

    kbd = Keyboard(usb_hid.devices)
    # エンコーダー・スイッチ類の初期設定
    encoder = rotaryio.IncrementalEncoder(PIN_A, PIN_B)
    
    center_push = digitalio.DigitalInOut(PIN_CENTER_PUSH)
    center_push.direction = digitalio.Direction.INPUT
    center_push.pull = digitalio.Pull.UP
    
    side_push = digitalio.DigitalInOut(PIN_TACTILE_SW)
    side_push.direction = digitalio.Direction.INPUT
    side_push.pull = digitalio.Pull.UP
    
    center_button = Button(center_push, on_center_short_press, on_center_long_press)
    side_button = Button(side_push, on_side_short_press, on_side_long_press)

    # 外部モジュール向けインターフェースの設定
    btms['kbd'] = kbd

    # オンラインアプリケーションの初期化
    layers = Layer()
    
    # 6Keys Dockの初期化
    dock6keys = Dock6Keys(on_dock6_key1_press, on_dock6_key2_press, on_dock6_key3_press, on_dock6_key4_press, on_dock6_key5_press, on_dock6_key6_press)
    
    # NeoPixelの初期設定
    led = NeoPixel(PIN_NEOPIXEL, 1, brightness=1.0)
    led_indicate(LED_INDICATOR_TOGGLE_MUTE_MODE)
    
    usb_cdc.console.timeout = 0.8


    while True:
        manage_knob()
        manage_led()
        manage_dock()
        center_button.poll()
        side_button.poll()
        command_input()
        if (attached_dock_type == DOCK_6KEYS):
            dock6keys.poll()
        
