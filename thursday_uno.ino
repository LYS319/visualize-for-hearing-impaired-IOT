#include <SoftwareSerial.h>

SoftwareSerial BTSerial(11, 10);

#define RED 4
#define GREEN 5
#define BLUE 6

int prevR = -1, prevG = -1, prevB = -1;

void setup() {
  BTSerial.begin(9600);
  Serial.begin(9600);
  pinMode(RED, OUTPUT);
  pinMode(GREEN, OUTPUT);
  pinMode(BLUE, OUTPUT);
}

void loop() {
  if (BTSerial.available()) {
    char ch = BTSerial.read();

    switch (ch) {
      case '0': setColor(0, 0, 0); break;
      case '1': setColor(255, 255, 255); break;
      case '2': setColor(0, 255, 0); break;
      case '3': setColor(0, 0, 255); break;
      case '4': setColor(255, 0, 0); break;
      default: break;
    }
  }
}

void setColor(int r, int g, int b) {
  if (r != prevR) analogWrite(RED, 255 - r);
  if (g != prevG) analogWrite(GREEN, 255 - g);
  if (b != prevB) analogWrite(BLUE, 255 - b);
  prevR = r; prevG = g; prevB = b;
}
