# AirGradient ONE mod: DFRobot CO sensor + buzzer

Fork of the AirGradient firmware (PlatformIO env `esp32-c3`, source `examples/OneOpenAir`) that adds a DFRobot SEN0466 CO sensor on I2C and a DFR0032 active buzzer on GPIO3 (HIGH = sound). All other behavior stays stock.

**Full hardware reference, pinouts, wiring, protocol, and diagnosis: `docs/co-sensor-mod.md`. Read it before touching hardware facts.**

## Status (2026-09-25)

- CO is exported as `"co"` in the local `/measures/current` JSON (not cloud). Build/flash/check via `make build`, `make flash`, `make check SERIAL=…`.
- Working on hardware: CO sensor on I2C1 (re-soldered), reading at 0x74, shown as `CO Nppm` in the OLED top row. Buzzer wired to the sensor's ALA pin; firmware sets the 50 ppm threshold at boot. The GPIO3 tone path was removed (git history has it) — rewire to IO3 only if time-weighted alarm rules are ever wanted.
- ALA pin proven to drive the buzzer. Its rule persists in the sensor across power cycles; firmware sets the 50 ppm rule (with retries, then alarm-off fallback) before the network step at every boot. Buzzer currently disconnected after a stuck test rule; recommendation is to wire green to IO3 instead of ALA.
- Serial reading from this Mac works: `.venv/bin/python <scratch>/serial_read.py <seconds>` (pyserial in the uv venv), port `/dev/cu.usbmodem1401`.
- Build needs `git submodule update --init --recursive`.
- 3D-printed sensor box: `docs/3d/` (generator; STLs are produced by it, not committed; clips onto the case's top sockets like the stand). `CELL_H` still needs a real measurement.

## Key facts

- I2C: SDA=GPIO7, SCL=GPIO6. OLED 0x3C, SHT4x 0x44, SGP41 0x59, CO sensor 0x74.
- GPIO3 is driven HIGH by stock `initializeNetwork()` (cellular reset line). The fork pulls it LOW on the first line of `setup()` and again right after that init; only `tone()` drives it.
- Keep GPIO2 watchdog feeding intact.
- OTA can't overwrite this build: the version string is unknown to the AirGradient server.

## About the user

Knows Python and VS Code, beginner with hardware and soldering. Wants short, direct, step-by-step answers in plain words, one clear path. Don't guess hardware facts; check the repo, the KiCad data, or datasheets, and say when something is unverified.

Safety: this is not a certified CO alarm. The user should keep a proper CO alarm.
