// Ultrasonic parking sensor - ELEGOO Super Starter Kit (UNO R3)
// HC-SR04 + LCD1602 (parallel, not I2C) + active buzzer + 3 LEDs
// No extra libraries needed: LiquidCrystal ships with the Arduino IDE.
//
// Serial Monitor / Plotter (9600 baud) prints CSV: ms,inches,zone
// so you can log a run and plot it in Python later.

#include <LiquidCrystal.h>

// ---------------- Pins ----------------
const byte TRIG_PIN   = 4;
const byte ECHO_PIN   = 5;
const byte BUZZER_PIN = 6;   // active buzzer (+ leg / longer leg)
const byte LED_GREEN  = 2;
const byte LED_YELLOW = 3;
const byte LED_RED    = 13;  // also lights the UNO's onboard "L" LED
LiquidCrystal lcd(7, 8, 9, 10, 11, 12);  // RS, E, D4, D5, D6, D7

// ---------------- Settings ----------------
const float STOP_IN    = 5.0;   // closer than this: solid buzzer, red LED
const float CAUTION_IN = 12.0;  // closer than this: beeping, yellow LED
const float HYST_IN    = 0.3;   // must move this far back out to leave a zone (stops flicker)
const float AIR_TEMP_C = 21.0;  // room temperature; speed of sound depends on it

const unsigned long ECHO_TIMEOUT_US  = 12000;  // ~2 m max range; no echo -> "out of range"
const unsigned long PING_INTERVAL_MS = 30;     // time between pings (lets old echoes die out)
const unsigned long LCD_INTERVAL_MS  = 200;    // LCD/serial refresh rate
const unsigned long BEEP_ON_MS       = 60;
const long BEEP_OFF_MIN_MS = 80;    // gap between beeps right at STOP_IN
const long BEEP_OFF_MAX_MS = 500;   // gap between beeps right at CAUTION_IN

// speed of sound (m/s) = 331.3 + 0.606 * T(C), converted to inches per microsecond
const float IN_PER_US = (331.3 + 0.606 * AIR_TEMP_C) * 39.3701 / 1000000.0;

// ---------------- State ----------------
enum Zone { SAFE, CAUTION, STOP };
Zone zone = SAFE;

const byte N_SAMPLES = 5;
float samples[N_SAMPLES];
byte sampleIdx = 0;
float distIn = -1.0;  // filtered distance, -1 = no valid reading

unsigned long lastPingMs = 0;
unsigned long lastLcdMs = 0;

// One HC-SR04 measurement in inches, or -1 if no echo came back.
float pingInches() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  unsigned long us = pulseIn(ECHO_PIN, HIGH, ECHO_TIMEOUT_US);
  if (us == 0) return -1.0;
  return us * IN_PER_US / 2.0;  // divide by 2: sound goes out and back
}

// Median of the last N valid samples; rejects one-off spikes.
float medianInches() {
  float v[N_SAMPLES];
  byte n = 0;
  for (byte i = 0; i < N_SAMPLES; i++) {
    if (samples[i] > 0) v[n++] = samples[i];
  }
  if (n < 3) return -1.0;
  for (byte i = 1; i < n; i++) {  // insertion sort
    float x = v[i];
    byte j = i;
    while (j > 0 && v[j - 1] > x) { v[j] = v[j - 1]; j--; }
    v[j] = x;
  }
  return v[n / 2];
}

// Enter a closer zone at its threshold; leave it only after backing off by HYST_IN.
Zone nextZone(float d, Zone cur) {
  if (d < 0) return SAFE;
  if (d < STOP_IN || (cur == STOP && d < STOP_IN + HYST_IN)) return STOP;
  if (d < CAUTION_IN || (cur != SAFE && d < CAUTION_IN + HYST_IN)) return CAUTION;
  return SAFE;
}

// SAFE: silent. CAUTION: beeps get faster as the object gets closer. STOP: solid tone.
void updateBuzzer(unsigned long now) {
  static bool on = false;
  static unsigned long lastToggle = 0;

  if (zone == SAFE) {
    on = false;
  } else if (zone == STOP) {
    on = true;
  } else {
    long offMs = map((long)(distIn * 10), (long)(STOP_IN * 10), (long)(CAUTION_IN * 10),
                     BEEP_OFF_MIN_MS, BEEP_OFF_MAX_MS);
    offMs = constrain(offMs, BEEP_OFF_MIN_MS, BEEP_OFF_MAX_MS);
    unsigned long wait = on ? BEEP_ON_MS : (unsigned long)offMs;
    if (now - lastToggle >= wait) {
      on = !on;
      lastToggle = now;
    }
  }
  digitalWrite(BUZZER_PIN, on ? HIGH : LOW);
}

void updateLeds() {
  digitalWrite(LED_GREEN,  zone == SAFE    ? HIGH : LOW);
  digitalWrite(LED_YELLOW, zone == CAUTION ? HIGH : LOW);
  digitalWrite(LED_RED,    zone == STOP    ? HIGH : LOW);
}

// Writes a full 16-char row so leftover characters from longer text get erased.
void lcdLine(byte row, const char *text) {
  lcd.setCursor(0, row);
  byte i = 0;
  for (; text[i] && i < 16; i++) lcd.print(text[i]);
  for (; i < 16; i++) lcd.print(' ');
}

const char *zoneName(Zone z) {
  if (z == STOP) return "STOP";
  if (z == CAUTION) return "CAUTION";
  return "SAFE";
}

void setup() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(LED_RED, OUTPUT);

  for (byte i = 0; i < N_SAMPLES; i++) samples[i] = -1.0;

  Serial.begin(9600);
  Serial.println(F("ms,inches,zone"));

  lcd.begin(16, 2);
  lcdLine(0, "Parking sensor");
  lcdLine(1, "Starting...");
  delay(1500);
}

void loop() {
  unsigned long now = millis();

  if (now - lastPingMs >= PING_INTERVAL_MS) {
    lastPingMs = now;
    samples[sampleIdx] = pingInches();
    sampleIdx = (sampleIdx + 1) % N_SAMPLES;
    distIn = medianInches();
    zone = nextZone(distIn, zone);
  }

  updateBuzzer(now);
  updateLeds();

  if (now - lastLcdMs >= LCD_INTERVAL_MS) {
    lastLcdMs = now;
    char line[17];
    if (distIn < 0) {
      lcdLine(0, "Dist:  --- in");
    } else {
      char num[8];
      dtostrf(distIn, 5, 1, num);
      snprintf(line, sizeof(line), "Dist: %s in", num);
      lcdLine(0, line);
    }
    if (zone == STOP) lcdLine(1, "STOP! Too close");
    else if (zone == CAUTION) lcdLine(1, "CAUTION");
    else lcdLine(1, "SAFE");

    Serial.print(now);
    Serial.print(',');
    Serial.print(distIn, 2);
    Serial.print(',');
    Serial.println(zoneName(zone));
  }
}
