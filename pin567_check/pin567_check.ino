/*
  Drive each of digital pins 5, 6, and 7 high and low, then read the pin
  back. A stuck pin cannot follow the order it was given.

  Then ask pins 5 and 6 for a half-on pulse and count both levels. Pin 7
  has no pulse hardware, so the same request must leave it sitting on.

  Pseudocode
    for pin in 5, 6, 7:
        drive high, read back
        drive low, read back
        let go, turn on the weak pull-up, read back
    for pin in 5, 6:
        request half-on pulse, sample, count high and low
        request fully off, sample, count high
    for pin 7:
        request half-on, sample, expect it to stay high
    release every pin
*/

const uint8_t PINS[] = {4, 5, 6, 7, 8};
const unsigned SAMPLE_LOOPS = 20000; 
//This code defines a constant array of pin numbers and a constant for the number of sample loops. It's not a universal C++ preamble, but common in Arduino sketches to make pin configurations and loop counts easy to reference and change.

void releasePins() {
  for (uint8_t pin : PINS) {
    pinMode(pin, INPUT);
  }
}

unsigned countHigh(uint8_t pin) {
  unsigned highs = 0;
  for (unsigned i = 0; i < SAMPLE_LOOPS; ++i) {
    if (digitalRead(pin)) {
      ++highs;
    }
  }
  return highs;
}

void reportLevel(uint8_t pin, const char *name, int reading) {
  Serial.print("PIN");
  Serial.print(pin);
  Serial.print(name);
  Serial.println(reading ? 1 : 0);
}

void setup() {
  Serial.begin(115200);
  delay(250);

  for (uint8_t pin : PINS) {
    pinMode(pin, OUTPUT);
    digitalWrite(pin, HIGH);
    delay(2);
    reportLevel(pin, "_OUT_HIGH=", digitalRead(pin));

    digitalWrite(pin, LOW);
    delay(2);
    reportLevel(pin, "_OUT_LOW=", digitalRead(pin));

    pinMode(pin, INPUT_PULLUP);
    delay(5);
    reportLevel(pin, "_PULLUP=", digitalRead(pin));
    pinMode(pin, INPUT);
  }

  for (uint8_t pin : PINS) {
    analogWrite(pin, 128);
    delay(5);
    unsigned highs = countHigh(pin);
    Serial.print("PIN");
    Serial.print(pin);
    Serial.print("_HALF_HIGHS=");
    Serial.print(highs);
    Serial.print("/");
    Serial.println(SAMPLE_LOOPS);

    analogWrite(pin, 0);
    delay(5);
    highs = countHigh(pin);
    Serial.print("PIN");
    Serial.print(pin);
    Serial.print("_OFF_HIGHS=");
    Serial.print(highs);
    Serial.print("/");
    Serial.println(SAMPLE_LOOPS);
  }

  releasePins();
  Serial.println("DONE");
}

void loop() {}
