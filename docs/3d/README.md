# CO sensor box for the AirGradient ONE

A printed box for the DFRobot SEN0466 that clips onto the **top edge** of the AirGradient ONE (I-9PSL V9)
the same way the official stand clips onto the bottom: the case has two identical hook sockets in its top
and bottom faces, 60 mm apart. The box has two hooks copied from AirGradient's stand model, so the fit is
the same as the stand's. The box is centred on the case with both hooks directly under its floor.

Files:

- `co_sensor_box.py` – generator. Everything is a parameter at the top of the file. It writes
  `co_sensor_box_body.stl` (closed back, floor, top, sides, hooks; open at the front) and
  `co_sensor_box_front.stl` (removable front plate with both openings and the buzzer posts).
  The STLs are not committed; run the generator (see below) when you need to print.

## v4 layout

- Outline like the AirGradient: all four corners of the front face rounded, square in the top view.
  73 mm wide, the minimum that keeps the hooks under flat floor inside the corner curves, 36.2 deep (the case depth), 40 high.
- **CO sensor** stands on four posts on the back wall, left, rotated 180° so the plug faces right and
  its cable drops through the left floor opening into the case. Its cell faces the round opening in
  the front plate.
- **Buzzer (DFR0032)** hangs on two posts on the inside of the front plate, right, 30 mm side
  horizontal, holes on its right edge, connector left. The 12 mm buzzer pokes through its opening.
  Cable through the right floor opening.
- The boards overlap 7 mm in width at different depths; the CO cell clears the buzzer board.
- Two floor openings exactly over the case's two vent slots between the sockets, and two matching slots in the top. No other holes.
- Buzzer dimensions from DFRobot's drawing: 22 × 30 mm, Ø3.2 holes 15 mm apart 3.4 mm from one
  short edge, buzzer centred 10.9 mm from that edge.

## Measured parts

CO cell: Ø23.34 mm, 26.1 mm above the PCB. Buzzer cylinder: Ø11.78 mm, 9.3 mm tall. Front openings
are cut 0.5 mm wider than the part; printed holes come out ~0.4 narrower, so a snug slip fit. Both
cylinders stand slightly proud of the plate. The generator prints the cell-to-buzzer clearance.

## Regenerate

```


.venv/bin/python docs/3d/co_sensor_box.py docs/3d/reference/airgradient-stand-stl.stl
```

Needs `uv pip install trimesh manifold3d shapely scipy networkx rtree numpy` in the project venv.

## Print

- **Body: stand it on its back wall** (closed end down, open front up). The rounded corners become
  vertical walls, nothing to support except the two small hooks, which the slicer handles with a
  little support. 0.2 mm layers, 3 walls, 20 % infill, PETG or PLA.
- **Front plate: flat, outside face down**, posts and lip up. No supports.
- Screw the CO sensor to the back-wall posts with M3 screws (self-tapping into 2.6 mm holes), plug to
  the right, DIP switch at the bottom. Screw the buzzer to the plate's posts, connector to the left.
  Both cables go down through the floor openings and the case's vent slots to the headers inside.
- Press the plate into the front; the lip holds it.

## Mount

Slide the box onto the top edge **from the back**, like the stand: the hooks enter the sockets from the
rear recess and slide forward about 6 mm under the lip. The box floor sits flat on the case's top face and
has slots over the case's vent slots so the case still breathes.

## Dimensions

| | mm |
|---|---|
| Box outside | 73 × 36.2 × 40 |
| Walls / floor / plate | 1.6 / 2.0 / 2.0 |
| CO posts | 30 × 25 grid on the back wall, Ø6, 4 high, 2.6 holes |
| Buzzer posts | 15 mm apart on the front plate, Ø6, 6.5 high, 2.6 holes |
| Front openings | Ø 23.84 (CO cell), Ø 12.28 (buzzer) in the file |
| Floor openings | 21 × 4, at the case's vent positions between the sockets |
| Hooks | 4 thick, 8.7 deep, 60 mm apart, profile copied from the stand; head top shaved for a 3.4 mm gap under the 3.0 mm lip |
