# AirGradient ONE mod: MLX90640 thermal camera

Fallback plan, not built. The camera runs on the Pi (smart-home repo, `bridges/thermal_bridge.py`, live since 2026-10-13). Move it here only if the monitor's spot has a view of the stove and the Pi's does not. Board facts come from `docs/co-sensor-mod.md`; read that first.

## Links

- Melexis MLX90640: <https://www.melexis.com/en/product/MLX90640/Far-Infrared-Thermal-Sensor-Array>
- Melexis C driver (EEPROM parameters, frame maths): <https://github.com/melexis/mlx90640-library>
- Adafruit Arduino library (wraps the Melexis driver): <https://github.com/adafruit/Adafruit_MLX90640>
- Pimoroni breakout: <https://shop.pimoroni.com/products/mlx90640-thermal-camera-breakout>

## Hardware

- Pimoroni MLX90640 breakout. Pins: `3-6V`, `SDA`, `SCL`, (blank, unused interrupt), `GND`.
- 32 × 24 pixels, I2C address `0x33`. Free on this bus (OLED `0x3C`, SHT4x `0x44`, SGP41 `0x59`, CO `0x74`).
- 3.3V supply is fine (range 3–6V), data lines are 3.3V.
- **Needs a direct line of sight.** Glass and the case block long-wave infrared. It can't see the stove through a window or from inside a box.

## Where it is now (Pi)

Pi 4 header, pins 1–6 block: `3-6V` → pin 1 (3.3V), `SDA` → pin 3, `SCL` → pin 5, `GND` → pin 6. Read over `/dev/i2c-1`, bus clock 400 kHz from `i2c_arm_baudrate` in `/boot/firmware/config.txt`.

## Wiring on the AirGradient

**I2C2** (spare, 4× 2.54 mm, unpopulated, needs a soldered header like I2C1). Its pin order differs from the breakout's, so match by name:

| I2C2 pad | Breakout pin |
|---|---|
| 1, 3.3V | `3-6V` |
| 2, GND | `GND` |
| 3, SCL | `SCL` |
| 4, SDA | `SDA` |
| — | blank: leave open |

**Fallback without soldering: IO1** (Molex PicoBlade 8P, 1.25 mm). Free since the buzzer moved to the CO sensor's ALA pin. Pin 3 = 3.3V, 2 = GND, 7 = SCL, 8 = SDA. Needs a crimped PicoBlade plug; a GH1.25 does not fit.

- **Cable ≤ 0.5 m.** The camera has to sit outside the case facing the stove, so it hangs on a cable. Long jumper wires make I2C unreliable, and this bus already lost the CO sensor once to bad joints.
- Mount: a variant of the printed sensor box (`docs/3d/`) with a window for the lens.

## Firmware (not written)

- `examples/OneOpenAir/OneOpenAir.ino`: probe `0x33`, load the calibration parameters from EEPROM once at boot, then read a frame every few seconds. Skip silently if absent.
- Use the Melexis maths (via the Adafruit library or the C driver). Raw pixels are meaningless without the EEPROM calibration.
- A full frame is two subpages, about 1 s at 2 Hz refresh. Read it in the loop without starving anything else. The TPL5010 watchdog must keep being fed.
- RAM: calibration parameters plus a 768-float frame, tens of KB at most. The ESP32-C3 has room.
- Keep the shared bus at its current speed. 100 kHz is enough for one frame every few seconds. Don't raise it for the camera at the other sensors' expense.

### Local API

- New endpoint `GET /thermal`: the 768 temperatures, row-major, rounded to 0.1 °C. About 4 KB as JSON.
- Keep it **off** `/measures/current`. The router's `airSample` script and the smart-home bridge poll that every 30–60 s and should stay small.

## smart-home side

`bridges/thermal_bridge.py` stays as it is apart from where frames come from:

- Replace `open_sensor()` / `sensor.getFrame(frame)` with an HTTP GET of `http://<monitor-ip>/thermal`.
- `summarize()` (max, mean, stove, person) and `render_png()` (the HA camera image) are unchanged.
- `docker-compose.yml`: remove the `/dev/i2c-1` device mapping from `thermal-bridge`.

Trade-off: one frame every few seconds instead of continuous 2 Hz. Fine for the stove (it heats over minutes), weak for spotting someone walking past.

## Moving it

1. Pi off. Unplug the camera from pins 1–6.
2. Solder a header on I2C2 (or crimp a PicoBlade for IO1).
3. Wire as above, camera outside the case, cable ≤ 0.5 m.
4. Flash the firmware. Check the boot log or `examples/I2CScan` for `0x33`.
5. `curl http://<monitor-ip>/thermal` should return 768 plausible temperatures (room ≈ 20–25 °C).
6. Switch the bridge to HTTP, deploy, and check the thermal image in HA to aim the camera.
