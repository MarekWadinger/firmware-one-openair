/*
 * I2C bus diagnostic for AirGradient ONE (ESP32-C3, SDA=GPIO7, SCL=GPIO6).
 *
 * Flash with platformio.ini:  src_dir = examples/I2CScan
 * Open the serial monitor at 115200. Every 2 s it prints:
 *   - the idle level of SDA/SCL (both must be HIGH; LOW = something holds the bus)
 *   - every I2C address that answers (expect 0x3C OLED, 0x44 SHT4x, 0x59 SGP41,
 *     and 0x74 for the DFRobot SEN0466 CO sensor)
 *   - a CO reading from 0x74 if the sensor answers
 */
#include <Arduino.h>
#include <Wire.h>

#define SDA_PIN 7
#define SCL_PIN 6
#define CO_ADDR 0x74

static uint8_t checksum(const uint8_t *p) {
  uint8_t s = 0;
  for (int i = 1; i <= 7; i++) s += p[i];
  return (~s) + 1;
}

static void readCo() {
  uint8_t cmd[9] = {0xFF, 0x01, 0x86, 0, 0, 0, 0, 0, 0};
  cmd[8] = checksum(cmd);
  Wire.beginTransmission(CO_ADDR);
  Wire.write((uint8_t)0);
  Wire.write(cmd, 9);
  if (Wire.endTransmission() != 0) { Serial.println("CO: write failed"); return; }
  delay(10);
  Wire.beginTransmission(CO_ADDR);
  Wire.write((uint8_t)0);
  if (Wire.endTransmission() != 0) { Serial.println("CO: read setup failed"); return; }
  uint8_t r[9] = {0};
  int n = Wire.requestFrom(CO_ADDR, 9);
  for (int i = 0; i < n && i < 9; i++) r[i] = Wire.read();
  Serial.printf("CO raw:");
  for (int i = 0; i < 9; i++) Serial.printf(" %02X", r[i]);
  Serial.println();
  if (n != 9 || checksum(r) != r[8]) { Serial.println("CO: bad checksum"); return; }
  float ppm = (r[2] << 8) | r[3];
  if (r[5] == 1) ppm *= 0.1f;
  if (r[5] == 2) ppm *= 0.01f;
  Serial.printf("CO: %.1f ppm (gas type 0x%02X, decimals %d)\n", ppm, r[4], r[5]);
}

void setup() {
  Serial.begin(115200);
  delay(2000);
  pinMode(SDA_PIN, INPUT_PULLUP);
  pinMode(SCL_PIN, INPUT_PULLUP);
  Serial.printf("Idle levels before Wire.begin: SDA=%d SCL=%d (1 = ok, 0 = held low)\n",
                digitalRead(SDA_PIN), digitalRead(SCL_PIN));
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setTimeOut(50);
}

// Count signal edges with I2C off. Nothing but the CO sensor can talk while the
// ESP is quiet, so edges on SDA mean the sensor is sending UART data (SEL = UART).
static void listenForUartChatter() {
  Wire.end();
  pinMode(SDA_PIN, INPUT_PULLUP);
  pinMode(SCL_PIN, INPUT_PULLUP);
  int sdaEdges = 0, sclEdges = 0;
  int sda = digitalRead(SDA_PIN), scl = digitalRead(SCL_PIN);
  uint32_t t0 = millis();
  while (millis() - t0 < 1500) {
    int s = digitalRead(SDA_PIN), c = digitalRead(SCL_PIN);
    if (s != sda) { sdaEdges++; sda = s; }
    if (c != scl) { sclEdges++; scl = c; }
  }
  Serial.printf("bus idle 1.5 s: SDA=%d SCL=%d, edges SDA=%d SCL=%d (0 = quiet, >0 = sensor is in UART mode)\n",
                sda, scl, sdaEdges, sclEdges);
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setTimeOut(50);
}

// If SEL is on UART, the sensor's TX is on the SDA wire and RX on the SCL wire.
// Send the same "read concentration" frame over UART at 9600 baud and listen.
static void probeUart(uint32_t baud, int rxPin, int txPin) {
  Wire.end();
  Serial1.begin(baud, SERIAL_8N1, rxPin, txPin);
  while (Serial1.available()) Serial1.read();
  uint8_t cmd[9] = {0xFF, 0x01, 0x86, 0, 0, 0, 0, 0, 0};
  cmd[8] = checksum(cmd);
  Serial1.write(cmd, 9);
  delay(200);
  int n = Serial1.available();
  Serial.printf("UART probe %lu baud rx=GPIO%d: %d bytes back", (unsigned long)baud, rxPin, n);
  if (n > 0) {
    Serial.print(" =");
    while (Serial1.available()) Serial.printf(" %02X", Serial1.read());
    Serial.print("  <-- sensor is ALIVE and SEL is on UART");
  }
  Serial.println();
  Serial1.end();
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setTimeOut(50);
}

// Full command frame to every candidate address (some MCU-based slaves ignore an
// empty address probe but answer a real command), at several bus speeds.
static void probeI2cFrames(uint32_t hz) {
  Wire.setClock(hz);
  for (uint8_t a = 0x74; a <= 0x77; a++) {
    uint8_t cmd[9] = {0xFF, 0x01, 0x86, 0, 0, 0, 0, 0, 0};
    cmd[8] = checksum(cmd);
    Wire.beginTransmission(a);
    Wire.write((uint8_t)0);
    Wire.write(cmd, 9);
    int w = Wire.endTransmission();
    delay(10);
    int n = Wire.requestFrom(a, (uint8_t)9);
    Serial.printf("I2C %lu Hz addr 0x%02X: write=%d (0=ack) read=%d bytes", (unsigned long)hz, a, w, n);
    if (n > 0) {
      Serial.print(" =");
      while (Wire.available()) Serial.printf(" %02X", Wire.read());
      Serial.print("  <-- sensor is ALIVE on I2C");
    }
    Serial.println();
  }
  Wire.setClock(100000);
}

void loop() {
  listenForUartChatter();
  probeI2cFrames(100000);
  probeI2cFrames(10000);
  probeUart(9600, SDA_PIN, SCL_PIN);   // normal: D/T on SDA
  probeUart(9600, SCL_PIN, SDA_PIN);   // swapped wires
  probeUart(115200, SDA_PIN, SCL_PIN);
  probeUart(19200, SDA_PIN, SCL_PIN);
  Serial.println("--- scan ---");
  int found = 0;
  for (uint8_t a = 1; a < 127; a++) {
    Wire.beginTransmission(a);
    if (Wire.endTransmission() == 0) {
      Serial.printf("found 0x%02X\n", a);
      found++;
      if (a == CO_ADDR) readCo();
    }
  }
  if (found == 0) Serial.println("nothing found (bus dead or held low)");
  delay(500);
}
