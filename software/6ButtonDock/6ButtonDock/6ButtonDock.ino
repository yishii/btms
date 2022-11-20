#include <Wire.h>
#include <FastLED.h>
#define NUM_LEDS 6
#define DATA_PIN 3

#define I2C_SLAVE_ADDR  0x48

const uint8_t SW_LUT[6] = {
  9, 4, 8, 7, 5, 6
};
const uint8_t LED_LUT[6] = {
  0, 3, 1, 4, 2, 5
};

bool updateLed = false;
CRGB leds[NUM_LEDS];
uint8_t pressedKeys = 0x00;

void requestEvent()
{
  Wire.write(pressedKeys);
}

void receiveEvent(int len)
{
  uint8_t data[4];
  if (len == 4)
  {
    for (int i = 0; i < 4; i++)
    {
      data[i] = Wire.read();
    }
    leds[LED_LUT[data[0]]] = CRGB(data[1], data[2], data[3]);
    updateLed = true;
  } else {
    while (len--) {
      Wire.read();
    }
  }
}

void boot_indicator(void)
{
  int i;
  int j;
  uint16_t b[6] = {0};
  const uint8_t pos_lut[6] = {
    0, 2, 4, 5, 3, 1
  };
  for (i = 0; i < 255; i++) {
    for (j = 0; j < 6; j++) {
      b[j] += j + 1;
      b[j] = b[j] > 255 ? 255 : b[j];
      leds[LED_LUT[pos_lut[j]]] = CRGB(b[j], b[j], b[j]);
    }
    FastLED.show();
    delay(3);
  }
  memset((void*)&b, 0, sizeof(b));
  for (i = 0; i < 255; i++) {
    for (j = 0; j < 6; j++) {
      b[j] += j + 1;
      b[j] = b[j] > 255 ? 255 : b[j];
      leds[LED_LUT[pos_lut[j]]] = CRGB(255 - b[j], 255 - b[j], 255 - b[j]);
    }
    FastLED.show();
    delay(3);
  }
  delay(60);
  for (i = 0; i < 6; i++) {
    leds[i] = CRGB(0, 0, 255);
  }
  FastLED.show();
  delay(50);
  for (i = 0; i < 6; i++) {
    leds[i] = CRGB(0, 0, 0);
  }
  FastLED.show();
  delay(50);
  for (i = 0; i < 6; i++) {
    leds[i] = CRGB(0, 0, 255);
  }
  FastLED.show();
  delay(50);
  for (i = 0; i < 6; i++) {
    leds[i] = CRGB(0, 0, 0);
  }
  FastLED.show();
  delay(50);
}

void setup() {
  Serial.begin(115200);
  Serial.println("resetting");
  FastLED.addLeds<WS2812, DATA_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(100);
  int i;
  boot_indicator();
  for (i = 0; i < 6; i++)
  {
    pinMode(SW_LUT[i], INPUT_PULLUP);
    leds[LED_LUT[i]] = CRGB(0, 0, 0);
  }
  FastLED.show();
  Wire.begin(I2C_SLAVE_ADDR);
  Wire.onRequest(requestEvent);
  Wire.onReceive(receiveEvent);
}

void loop()
{
  static int cnt = 0;
  int i;
  uint8_t pressed;
  static uint8_t pressed_last;
  pressed = 0;
  for (i = 0; i < 6; i++)
  {
    if (digitalRead(SW_LUT[i]) == LOW) {
      pressed |= (1 << i);
    }
  }
  if (pressed == pressed_last)
  {
    cnt++;
    if (cnt > 3) {
      noInterrupts();
      {
        pressedKeys = pressed;
      }
      interrupts();
      cnt = 0;
    }
  } else {
    cnt = 0;
  }
  pressed_last = pressed;
  Serial.println(pressedKeys, BIN);

  if (updateLed)
  {
    FastLED.show();
  }
  delay(1);
}
