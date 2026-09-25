# AirGradient ONE mod: DFRobot CO sensor + buzzer

## Goal

Modify the original AirGradient firmware in this repo (PlatformIO env `esp32-c3`, source `examples/OneOpenAir`) to:

1. Read a **DFRobot SEN0466** CO sensor over I2C and show CO (ppm) on the OLED.
2. Drive a **DFRobot DFR0032** buzzer on **GPIO3** when CO exceeds a threshold.
Keep all original behavior (dashboard, app, screen, LED bar) otherwise unchanged.

## Hardware: AirGradient ONE, model I-9PSL, PCB V9

Pinouts below come from AirGradient's official KiCad board file:

- **I2C1** (4 holes): 1=3.3V, 2=GND, 3=SCL, 4=SDA. It shares one I2C bus with the OLED (0x3C), SHT4x (0x44), and SGP41 (0x59). I2C2, I2C3, SHT1 and the first 4 pins of BME are the same bus.
- **IO1** (Molex PicoBlade 1.25 mm, 8 pins): 1=5V, 2=GND, 3=3.3V, 4=IO5, 5=IO4, 6=IO3, 7=SCL, 8=SDA. IO3/IO4/IO5 run only to IO1 and the ESP32-C3.
- The ESP32-C3's I2C is believed to be **SDA=GPIO7, SCL=GPIO6**. Verify in the repo's board definitions.
- Con1/Con2 are not connected to the MCU. Ignore them.

## Wiring done by the user

- **CO sensor:** male header soldered into I2C1. This was the user's first soldering: the solder mask near the holes got scorched, but the pads are intact and no bridges are visible. Wires: `+`→3.3V, `−`→GND, `C/R`→SCL, `D/T`→SDA.
- **Buzzer:** connected to IO1 via a PicoBlade cable. Red→5V, black→GND, green (signal)→IO3. It buzzed constantly with the stock firmware (GPIO3 floating). The user was told to pull the signal wire off until the firmware drives GPIO3.

## Component notes

- **SEN0466:** use the `DFRobot_MultiGasSensor` library. The default I2C address is **0x74** (DIP A0=A1=0; the range is 0x74–0x77). DIP `SEL`: 0=I2C, 1=UART. The actual lever position hasn't been confirmed. The ALA (alarm) pin is unused. `setThresholdAlarm()` exists, but whether it persists across power cycles is undocumented.
- **DFR0032:** a **passive** buzzer. It needs a square wave (`tone()`/LEDC), not a steady HIGH. It runs on 3.3–5V.

## CURRENT PROBLEM: solve this first

- With the CO sensor's data lines (C/D) connected, the device **doesn't boot** (the display never starts).
- Hot-plugging the sensor while running **garbles the display**.
- Power only (+/− connected, C/D off) boots fine. Without the sensor the board works normally.
- It fails in **both** SEL positions. Something blinks red in one position (unclear which part).
- Suspects: the sensor holding SDA/SCL low or disturbing the bus, mode/address, or a trace damaged near I2C1 during soldering.

**Next step:** flash an I2C scan sketch (`examples/I2CScan/I2CScan.ino`, temporarily pointing `src_dir` in `platformio.ini` at it), run it with the sensor connected, and check whether the scan hangs and whether 0x74 appears. Then add the CO reading, the display, and the buzzer to `OneOpenAir`.

## About the user

The user knows Python and uses VS Code, but is a beginner with hardware and soldering. They want **short, direct, step-by-step answers in plain words**, with one clear path rather than many options. Don't guess hardware facts; check the repo, the datasheets, or the KiCad data.

Hardware safety note: this CO setup is not a certified alarm. The user should keep a proper CO alarm.
