#include <SoftwareSerial.h>

SoftwareSerial BTSerial(19, 18);

const int ledPins[10] = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11};
const int soundPin = A0;

unsigned long lastTime = 0;
unsigned long nowTime = 0;
unsigned long interval = 0;

void setup() {
  Serial.begin(9600);
  BTSerial.begin(9600);

  for (int i = 0; i < 10; i++) {
    pinMode(ledPins[i], OUTPUT);
    digitalWrite(ledPins[i], LOW);
  }

  Serial.println("System Start");
  lastTime = millis();
}

void loop() {
  nowTime = millis();
  interval = nowTime - lastTime;
  lastTime = nowTime;

  int adcValue = analogRead(soundPin);
  if (adcValue < 80) adcValue = 0;

  int zone = calculateZone(adcValue);
  int ledCount = zone * 2;
  if (ledCount > 10) ledCount = 10;

  controlLED(ledCount);
  int colorZone = calculateColorZone(ledCount);
  BTSerial.println(colorZone);

  Serial.print("Interval: ");
  Serial.print(interval);
  Serial.print(" ms | ADC: ");
  Serial.print(adcValue);
  Serial.print(" | Zone: ");
  Serial.print(zone);
  Serial.print(" | LED Count: ");
  Serial.print(ledCount);
  Serial.print(" | Color Zone: ");
  Serial.println(colorZone);

  delay(100);
}

int calculateZone(int adcValue) {
  if (adcValue == 0) return 0;
  else if (adcValue < 200) return 1;
  else if (adcValue < 300) return 2;
  else if (adcValue < 380) return 3;
  else if (adcValue < 450) return 4;
  else return 5;
}

int calculateColorZone(int ledCount) {
  if (ledCount == 0) return 0;
  else if (ledCount <= 3) return 1;
  else if (ledCount <= 6) return 2;
  else if (ledCount <= 9) return 3;
  else return 4;
}

void controlLED(int ledCount) {
  for (int i = 0; i < 10; i++) {
    if (i < ledCount) digitalWrite(ledPins[i], HIGH);
    else digitalWrite(ledPins[i], LOW);
  }
}
