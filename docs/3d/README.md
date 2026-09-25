# CO sensor box for the AirGradient ONE

A printed box for the DFRobot SEN0466 that clips onto the **top edge** of the AirGradient ONE (I-9PSL V9)
the same way the official stand clips onto the bottom: the case has two identical hook sockets in its top
and bottom faces, 60 mm apart. The box has two hooks copied from AirGradient's stand model, so the fit is
the same as the stand's. The box is centred on the case with both hooks directly under its floor.

Files:

- `co_sensor_box_body.stl` – box with hooks and rail
- `co_sensor_box_lid.stl` – friction-fit lid with vent slots
- `co_sensor_box.py` – generator. Everything is a parameter at the top of the file.

## v3 layout

- **CO sensor** stands upright against the back wall on four posts, hard left, rotated 180° so the
  Gravity plug faces right and its cable drops through the left floor opening into the case. Its cell
  faces forward through a round opening in the front wall.
- **Buzzer (DFR0032)** hangs on two posts on the inner face of the front wall, hard right, 30 mm side
  horizontal, holes on its right edge, connector on its left edge. The 12 mm buzzer pokes through its
  own opening in the front wall. Its cable drops through the right floor opening.
- The two boards overlap 0.7 mm in width but sit at different depths (back wall vs front wall).
- The box is exactly as deep as the case (36.2 mm). The two floor openings sit exactly over the case's
  two vent slots between the sockets, and both cables pass through them into the case. No other holes.
- Buzzer dimensions come from DFRobot's drawing: 22 × 30 mm, Ø3.2 holes 15 mm apart 3.4 mm from one
  short edge, buzzer centred 10.9 mm from that edge.

## Before printing: measure two things

- `CELL_D`: diameter of the black cell, default 21 mm. The front opening is 2 mm larger.
- `CELL_H`: height of the cell above the board, default 22 mm. Up to 27 mm fits inside; taller pokes
  through the opening, which is fine.

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
- Screw the sensor to the four posts on the back wall with M3 screws (self-tapping into 2.6 mm holes),
  plug to the right, DIP switch at the bottom. Screw the buzzer to the two posts on the front wall,
  buzzer through the front opening, connector to the left. Both cables go down through the floor
  openings and the case's vent slots to the headers inside the case.

## Mount

Slide the box onto the top edge **from the back**, like the stand: the hooks enter the sockets from the
rear recess and slide forward about 6 mm under the lip. The box floor sits flat on the case's top face and
has slots over the case's vent slots so the case still breathes.

## Dimensions

| | mm |
|---|---|
| Box outside | 70 × 36.2 × 38 (+2 lid) |
| Walls / floor | 1.6 / 2.0 |
| Board posts | 30 × 25 grid on the back wall, Ø6, 4 high, 2.6 holes |
| Floor openings | 21 × 4, at the case's vent positions between the sockets |
| Front openings | Ø CELL_D + 2 (CO cell), Ø 14 (buzzer) |
| Buzzer posts | 15 mm apart on the front wall, Ø6, 6 high, 2.6 holes |
| Hooks | 4 thick, 8.7 deep, at 60 mm spacing, profile copied from the stand |

The Gravity plug faces left (viewer's left when facing the display). The spare room on the left of the
board fits the DFR0032 buzzer if you want it inside the box.
