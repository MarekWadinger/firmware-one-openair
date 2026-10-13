# AirGradient ONE mod: GY-BME/PMP280 pressure sensor

Planned, not built. A GY-BME/PMP280 breakout on the board's unpopulated `BME` footprint. Board facts come from `docs/co-sensor-mod.md`; read that first.

## Links

- Bosch BME280 (pressure, temperature, humidity): <https://www.bosch-sensortec.com/products/environmental-sensors/humidity-sensors-bme280/>
- Bosch BMP280 (pressure, temperature): <https://www.bosch-sensortec.com/products/environmental-sensors/pressure-sensors/bmp280/>
- Forum thread on adding a BMP580 to the ONE V9: <https://forum.airgradient.com/t/adding-bmp580-to-airgradient-one-v9-io1-connector-and-firmware-support/6732/3>

## Which chip is on the board

"GY-BME/PMP280" breakouts carry either a BME280 or a BMP280, and sellers mix them up. Read register `0xD0` (chip ID):

| ID | Chip | Measures |
|---|---|---|
| `0x60` | BME280 | pressure, temperature, humidity |
| `0x58` | BMP280 | pressure, temperature |

## Wiring

The `BME` footprint is a 6× 2.54 mm row, unpopulated, so it needs a soldered header like I2C1. Its first four pads match the breakout's first four pins:

| AG `BME` pad | Breakout pin |
|---|---|
| 1, 3.3V | VCC |
| 2, GND | GND |
| 3, SCL | SCL |
| 4, SDA | SDA |
| 5, NC | CSB |
| 6, NC | SDO |

- **Orientation:** pad 1 is 3.3V. Check it with a multimeter before soldering; reversed, VCC sits on GND.
- **3.3V only.** The 6-pin GY boards have no regulator. The footprint supplies 3.3V, which is correct.
- **CSB must be high for I2C.** Pads 5 and 6 are not connected, so the board's own pull-up has to do it. Most GY boards have one. If CSB is pulled low even once, the chip switches to SPI until the next power cycle. If the sensor doesn't show in a scan, check CSB first.
- **SDO sets the address:** low = `0x76`, high = `0x77`. Both are free on this bus (OLED `0x3C`, SHT4x `0x44`, SGP41 `0x59`, CO `0x74`). Don't set the CO sensor's DIP switches to `0x76`/`0x77`.
- The breakout adds its own SDA/SCL pull-ups in parallel with the board's. Fine for one extra board.

## What it adds

- **Pressure.** The only new measurement. Absolute accuracy about ±1 hPa, relative about ±0.12 hPa (12 Pa). Good for a barometer graph and weather trends.
- **Temperature and humidity: nothing.** The SHT4x already measures both, more accurately. The BMx280 also reads warm from its own heating. Ignore those values.

## Caveat: not useful for air-exchange identification

Air flow through windows and doors is driven by indoor–outdoor pressure differences of a few pascals:

- stack effect: about 0.04 Pa per metre of height per kelvin of temperature difference, so roughly 2 Pa for a 3 m room at 20 K;
- wind: a few Pa on a typical day.

Measuring that would need a second sensor outdoors and comparing the two. The offset between two BMx280s (about ±12 Pa, plus drift with temperature) is larger than the signal. The weather also moves absolute pressure by hundreds of pascals per day, so the difference has to be taken at the same instant.

For indoor–outdoor ΔP use a differential pressure sensor with a tube through the envelope, e.g. Sensirion SDP810 (125 Pa range).

## Firmware (not written)

Stock firmware does not read this footprint. To do, in the style of the CO sensor changes:

- `examples/OneOpenAir/OneOpenAir.ino`: probe `0x76`/`0x77`, check the chip ID, read pressure on the existing 2 s cycle. Skip silently if absent, so the build still runs without the board.
- Add `"pressure"` (hPa) to the local server JSON, like `"co"`.
- smart-home repo: map `pressure` in the AirGradient bridge to Home Assistant `device_class: atmospheric_pressure`.
