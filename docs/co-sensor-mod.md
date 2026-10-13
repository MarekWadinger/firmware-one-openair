# AirGradient ONE mod: DFRobot CO sensor + buzzer

Hardware reference for the custom build in this fork. Pin facts come from the official KiCad board file (`ag-diy-pro.kicad_pcb` in the I-9PSL KiCad zip). Firmware facts come from this repo.

## Links

- Upstream firmware: <https://github.com/airgradienthq/arduino>
- ONE V9 knowledge base, with a labeled PCB component image: <https://www.airgradient.com/documentation/kb/one-v9>
- Builds overview with KiCad/Gerber downloads: <https://www.airgradient.com/documentation/kb/kb-diy-the-airgradient-builds-overview>
- KiCad files for I-9PSL: <https://www.airgradient.com/documents/gerber/v9/I-9PSL_KiCad.zip>
- Forum thread on IO1/I2C1/I2C2 (I2C1/I2C2 need soldering, IO1 is Molex PicoBlade 1.25 mm 8P, a GH1.25 plug did not fit): <https://forum.airgradient.com/t/adding-bmp580-to-airgradient-one-v9-io1-connector-and-firmware-support/6732/3>
- DFRobot gas sensor wiki (SEN0465–SEN0476): <https://wiki.dfrobot.com/SKU_SEN0465toSEN0476_Gravity_Gas_Sensor_Calibrated_I2C_UART>
- DFRobot threshold alarm example: <https://wiki.dfrobot.com/sen0465/docs/21905>
- DFRobot library (protocol reference; not used by this build): <https://github.com/DFRobot/DFRobot_MultiGasSensor>

## Board: AirGradient ONE, model I-9PSL, PCB V9

### ESP32-C3-MINI-1 GPIO map

| GPIO | Use |
| --- | --- |
| IO0 / IO1 | RX_2 / TX_2, SenseAir S8 CO2 (UART) |
| IO2 | WD_RST, TPL5010 hardware watchdog. Firmware must keep feeding it. |
| **IO3** | Free. Goes only to IO1 pin 6. **Buzzer.** Stock firmware drives it HIGH in `initializeNetwork()` as the cellular-card reset line. |
| IO4, IO5 | Free. Go only to IO1 pins 5 and 4. |
| **IO6** | **SCL**, shared I2C bus |
| **IO7** | **SDA**, shared I2C bus |
| IO8 | Strapping pin, pulled on board |
| IO9 | BOOT button |
| IO10 | LED bar data |
| IO18 / IO19 | USB D− / D+ |
| IO20 / IO21 | RX_1 / TX_1, PMS particle sensor (UART) |

Both hardware UARTs are taken (CO2 + PMS), so the CO sensor must use I2C.

### Connectors

| Ref | Type | Pins | Notes |
| --- | --- | --- | --- |
| **I2C1** | 4× 2.54 mm through-hole, unpopulated | 1=3.3V, 2=GND, 3=SCL, 4=SDA | **CO sensor is here.** Near SHT1. |
| I2C2 | 4× 2.54 mm, unpopulated | 1=3.3V, 2=GND, 3=SCL, 4=SDA | Spare, identical. Same row as I2C3/BME. |
| I2C3 | 4× 2.54 mm socket | 3.3V, GND, SCL, SDA | SGP41 TVOC/NOx module |
| SHT1 | 4× 2.54 mm socket | 3.3V, GND, SCL, SDA | SHT4x temp/humidity module |
| BME | 6× 2.54 mm, unpopulated | 3.3V, GND, SCL, SDA, NC, NC | Unsupported by firmware. Planned pressure sensor: `docs/pressure-sensor-mod.md` |
| OLED1 | 4× 2.54 mm socket | 5V, GND, SCL, SDA | Display, 0x3C |
| **IO1** | Molex PicoBlade 53261-0871, 8P 1.25 mm | 1=5V, 2=GND, 3=3.3V, 4=IO5, 5=IO4, 6=IO3, 7=SCL, 8=SDA | **Buzzer is here** (pins 1, 2, 6). Pins 3, 2, 7, 8 are a soldering-free fallback for the CO sensor if I2C1 is damaged. |
| PM2 | Same PicoBlade 8P | 1=5V, 2=GND, 4=TX_1, 5=RX_1 | Particle sensor. Looks identical to IO1, do not confuse. |
| Co2-S8 | SenseAir S8 footprint | 5V, GND, TX_2, RX_2 | CO2 sensor |
| Con1, Con2, RS1 | 2× 4-pin sockets + "Modbus" screw terminal | wired only to each other | Not connected to the MCU. Ignore. |
| USB1 | USB-C | power + native USB | Flashing and serial. Hold Boot while plugging in if upload won't start. |
| U2 | TPL5010 | watchdog → EN | |
| U4 | LM1117-3.3 | 5V → 3.3V | |
| F1 | 1A fuse | USB 5V | |

I2C addresses on the bus: OLED 0x3C, SHT4x 0x44, SGP41 0x59, CO sensor 0x74 (range 0x74–0x77). No conflict.

## Parts

### DFRobot SEN0466, Gravity CO sensor, I2C and UART

- Gravity 4-pin plug: `+`, `−`, `C/R` (SCL in I2C, RX in UART), `D/T` (SDA in I2C, TX in UART).
- 5-hole row: VCC, GND, V0, ALA, NA. `ALA` goes HIGH while the alarm rule set with command 0x89 is true, LOW otherwise. **The rule persists in the sensor across power cycles**, and the sensor occasionally NACKs the 0x89 command, so the firmware retries it at every boot and switches the alarm off if all retries fail. Never leave a test rule active (a "below N" rule with N above room level keeps ALA high forever). The sensor's controller can also hang; pulling `+` for 5 s restarts it.
- DIP switch, 3 levers: `SEL`, `A1`, `A0`. SEL 0 = I2C, 1 = UART. A0/A1 pick the address, both 0 = 0x74. Which lever position is "0" has not been confirmed on the physical part.
- Electrochemical, needs warm-up. Supply 3.3–5 V.
- I2C protocol (from the DFRobot library): 9-byte frames `FF 01 cmd d0 d1 d2 d3 d4 checksum`, checksum = two's complement of the sum of bytes 1..7. Write the frame to register 0, wait 10 ms, read 9 bytes from register 0. Command 0x78 arg 0x04 = passive mode. Command 0x86 = read concentration: reply bytes 2..3 = value, byte 4 = gas type (0x04 = CO), byte 5 = number of decimals.

### DFRobot DFR0032, digital buzzer module V2

- Active buzzer. The DFRobot datasheet says "use High/Low to drive it": HIGH = continuous sound. `tone()` works too and gives the beep pattern. GPIO3 must be LOW from the first line of `setup()`, and again after `agSerial->init()` raises it.
- 3.3–5 V. Cable: red = +, black = −, green = signal.

## Wiring as built (final, 2026-09-25)

- CO sensor → I2C1 via a soldered male 2.54 mm header. The first attempt had bad SCL/SDA joints (sensor unreachable); a colleague re-soldered it and it works. `+`→3.3V, `−`→GND, `C/R`→SCL, `D/T`→SDA.
- Buzzer → the sensor's own 5-hole row: red→VCC, black→GND, green→ALA. The sensor drives the alarm itself; the firmware sets the 50 ppm threshold at every boot. GPIO3 / IO1 are no longer used for the buzzer, but the firmware still drives GPIO3 as a buzzer output, so either wiring works.

## Firmware changes in this fork

- `examples/OneOpenAir/OneOpenAir.ino`: reads CO every 2 s with raw `Wire` calls (no library added), sets the sensor to passive mode at boot, pulls GPIO3 LOW after `initializeNetwork()`, beeps 1 s per cycle while CO ≥ `CO_ALARM_PPM` (50). Settings are `#define`s near the top.
- `src/AgOledDisplay.{h,cpp}`: `OledDisplay::co` member, drawn as "CO nn" in the dashboard top row between temperature and humidity. Not drawn while a WiFi/cloud status icon occupies that space.
- `platformio.ini`: `aglib=symlink://${PROJECT_DIR}` instead of `../arduino`, so the repo folder can have any name.
- `examples/I2CScan/I2CScan.ino`: bus diagnostic. Build without editing `platformio.ini`:

  ```
  PLATFORMIO_SRC_DIR=examples/I2CScan PLATFORMIO_BUILD_DIR=.pio/build-scan pio run -e esp32-c3 -t upload && pio device monitor
  ```

Build requires `git submodule update --init --recursive` and a git clone (the version string comes from `git describe`).

### OTA safety

The device asks `hw.airgradient.com` for updates at boot and hourly, sending its version string. This build reports `3.7.0-<n>-g<hash>-dirty` (see `git describe --tags --always --dirty`), which the server does not know, so it answers 400 and does not overwrite the build (see `docs/ota-updates.md`). If a future upstream change alters that, set "cloud connection disabled" in the local config, which skips the update check entirely.

The AirGradient cloud dashboard has no CO field. CO is shown on the OLED only.

## Boot problem, diagnosed (2026-09-25)

Cause of the original "no display": `setup()` probes 0x3C to detect the board type. If the OLED is not found, the firmware assumes an outdoor unit and never initializes the display.

Tests with `examples/I2CScan` (all four sensor wires on I2C1, both SEL positions, sensor power-cycled after each flip), read over USB serial:

| Probe | Result |
|---|---|
| SDA/SCL idle level | Both HIGH, bus healthy |
| I2C scan 1–126 | Only 0x3C, 0x44, 0x59. Never 0x74–0x77 |
| Full DFRobot command frame to 0x74–0x77 at 100 kHz and 10 kHz | Address NACK, no reply |
| Passive listen for UART chatter on SDA/SCL, 1.5 s windows | Never an edge |
| UART query at 9600 (normal and swapped wires), 19200, 115200 | 0 bytes back |

Then the same four wires on I2C2 with an unsoldered header pressed into the holes: the sensor answered at 0x74 immediately, gas type 0x04 (CO), valid checksum, 0–2 ppm in room air.

**Conclusion: the sensor is fine and in I2C mode. The I2C1 solder joints were the fault.** Fixed by re-soldering I2C1. The sensor has no indicator LED, so "no light" was never evidence.

Occasional board reboots seen when wires were pushed onto I2C1 are not the sensor (it draws under 5 mA); most likely a momentary short between pins 1 and 2.

## Safety

This is not a certified CO alarm. Keep a proper CO alarm.
