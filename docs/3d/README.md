# CO sensor box for the AirGradient ONE

A printed box for the DFRobot SEN0466 that clips onto the **top edge** of the AirGradient ONE (I-9PSL V9)
the same way the official stand clips onto the bottom: the case has two identical hook sockets in its top
and bottom faces, 60 mm apart. The box has two hooks copied from AirGradient's stand model, so the fit is
the same as the stand's. The box is centred on the case with both hooks directly under its floor.

Files:

- `co_sensor_box_body.stl` – box with hooks and rail
- `co_sensor_box_lid.stl` – friction-fit lid with vent slots
- `co_sensor_box.py` – generator. Everything is a parameter at the top of the file.

## Before printing: measure one thing

`CELL_H` in the script is the height of the sensor's black cylindrical cell above the board, default 22 mm.
Measure it with a ruler (board top surface to top of the cell). If it's more than 22 mm, change the number
and regenerate.

## Regenerate

```
curl -sL -o /tmp/stand.zip https://www.airgradient.com/documents/diy-pro/airgradient-stand-stl.zip
unzip -o /tmp/stand.zip -d /tmp/stand
.venv/bin/python docs/3d/co_sensor_box.py /tmp/stand/airgradient-stand-stl.stl
```

Needs `uv pip install trimesh manifold3d shapely scipy networkx rtree numpy` in the project venv.

## Print

- **Body: lay it on its back face**, the flat side with the cable notch, so the hooks grow straight up
  from the bed. No supports needed. 0.2 mm layers, 3 walls, 20 % infill, PETG or PLA.
- **Lid: flat, lip up.** No supports.
- Fit the sensor on the four posts with M3 screws (self-tapping into 2.6 mm holes). Gravity plug faces
  left; the cable runs along the left wall, out through the rear notch, and down the case's recessed back.

## Mount

Slide the box onto the top edge **from the back**, like the stand: the hooks enter the sockets from the
rear recess and slide forward about 6 mm under the lip. The box floor sits flat on the case's top face and
has slots over the case's vent slots so the case still breathes.

## Dimensions

| | mm |
|---|---|
| Box outside | 70 × 36.2 × 31.6 (+2 lid) |
| Walls / floor | 1.6 / 2.0 |
| Board posts | 30 × 25 grid, Ø6, 4 high, 2.6 holes |
| Hooks | 4 thick, 8.7 deep, at 60 mm spacing, profile copied from the stand |

The Gravity plug faces left (viewer's left when facing the display). The spare room on the left of the
board fits the DFR0032 buzzer if you want it inside the box.
