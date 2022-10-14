#include <FastLED.h>
#define NUM_LEDS 6
#define DATA_PIN 3

const uint8_t SW_LUT[6] = {
  9, 4, 8, 7, 5, 6
};
const uint8_t LED_LUT[6] = {
  0, 3, 1, 4, 2, 5
};

CRGB leds[NUM_LEDS];

void setup() {
  Serial.begin(57600);
  Serial.println("resetting");
  FastLED.addLeds<WS2812, DATA_PIN, RGB>(leds, NUM_LEDS);
  FastLED.setBrightness(84);
  int i;
  for (i = 0; i < 6; i++)
  {
    pinMode(SW_LUT[i], INPUT_PULLUP);
  }
}

void loop() {
  int i;
  static uint8_t hue = 0;
  for (i = 0; i < 6; i++)
  {
    if (digitalRead(SW_LUT[i]) == LOW) {
      leds[LED_LUT[i]] = CHSV(0, 255, 255);
    } else {
      leds[LED_LUT[i]] = CHSV(100, 255, 255);
    }
  }
  FastLED.show();

}
