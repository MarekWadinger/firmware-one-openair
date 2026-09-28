PORT ?= /dev/cu.usbmodem1401
DEVICE ?= airgradient_$(SERIAL).local

.PHONY: build flash monitor check

## Compile the esp32-c3 firmware
build:
	pio run -e esp32-c3

## Compile and upload over USB (plug the device into this Mac first)
flash:
	pio run -e esp32-c3 -t upload --upload-port $(PORT)

## Serial console
monitor:
	pio device monitor -p $(PORT) -b 115200

## Verify the local API exposes CO: make check SERIAL=<serial> (or DEVICE=<ip>)
check:
	curl -s http://$(DEVICE)/measures/current | python3 -m json.tool | grep -E '"(co|serialno|firmware)"'
