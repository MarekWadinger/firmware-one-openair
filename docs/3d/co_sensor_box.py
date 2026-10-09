"""
3D-printable box for the DFRobot SEN0466 CO sensor, clipping onto the top edge
of the AirGradient ONE (I-9PSL V9) case the same way the official stand clips
onto the bottom: two hooks into the case's sockets. The tongue geometry is
cut straight out of AirGradient's stand STL, so the fit is the same.

Usage:  .venv/bin/python docs/3d/co_sensor_box.py <path to airgradient-stand-stl.stl>
Output: docs/3d/co_sensor_box_body.stl, docs/3d/co_sensor_box_front.stl

Box frame: X = across the case (viewer's left is -X), Y = case depth (front is -Y),
Z = up from the case's top face. v4: the box is a tube with the AirGradient's kind of curvature
(rounded corners on the front face, square in the top view), as wide as the hook spacing, closed at
the back and open at the front. The CO sensor stands on the back wall, left; the DFR0032 buzzer hangs
on the removable front plate, right, through its own opening. Both cables drop through the floor.
"""
import sys
import numpy as np
import trimesh
from shapely.geometry import box as sbox, Polygon
from shapely.affinity import translate

# ---- tunables (mm) --------------------------------------------------------
CELL_H = 26.1      # height of the cell above the PCB (measured)
CELL_D = 23.34     # diameter of the cell (measured)
WALL = 1.6
FLOOR = 2.0
PLATE_T = 2.0      # front plate
PLATE_LIP = 3.0
CLEAR = 0.2
BOARD_W, BOARD_H = 37.0, 32.0     # DFRobot CO board, standing: 37 across (X), 32 tall (Z)
HOLE_DX, HOLE_DZ = 30.0, 25.0
STANDOFF_H, STANDOFF_D, SCREW_D = 7.4, 6.0, 2.6   # 7.4 puts the cell face 0.5 mm proud of the plate
MARGIN = 0.5       # boards this far from the side walls (the back wall is flat, the posts clear the top curves)
CORNER_R = 7.5     # corners of the front face; same proportion as the case (13.5 on 131)
OUT_H = 40.0
# DFRobot DFR0032 buzzer (dimension drawing): 22 x 30 board, two 3.2 holes 15 apart 3.4 in from one
# short edge, 12 mm buzzer centred 10.9 from that edge, connector on the other edge.
BUZZ_W, BUZZ_H = 30.0, 22.0       # 30 mm side horizontal, holes on the right edge, connector left
BUZZ_HOLE_DZ, BUZZ_HOLE_IN, BUZZ_SCREW_D = 15.0, 3.4, 2.6
BUZZ_D, BUZZ_CYL_IN, BUZZ_CYL_H = 11.78, 10.9, 9.3   # diameter and height measured
BUZZ_POST_H = 6.5                 # board this far behind the front plate; buzzer ends 0.5 mm behind the plate face
CELL_OPEN_CLEAR = 0.5             # front openings: file = part + 0.5; prints ~0.4 narrower, snug
BUZZ_OPEN_CLEAR = 0.5

# ---- from the case STL (case coordinates) ---------------------------------
SOCKET_Y = (-112.5, -52.5)        # socket centres, 60 mm apart, same top and bottom
HOOK_W = 4.0
LIP_T = 3.0                       # case lip the hook head slides under (from the case model, confirmed on the real unit)
HOOK_GAP_CLEAR = 0.4              # printed slots come out ~0.2 narrow; 3.4 modelled -> ~3.2 printed
CASE_FRONT_Z, CASE_BACK_Z = -15.6, 20.6
CASE_VENTS_BETWEEN_SOCKETS = [(-108.0, -87.0), (-78.0, -57.0)]
VENT_Z = (-2.0, 2.0)

# ---- derived --------------------------------------------------------------
HOOK_EDGE_MARGIN = 4.5            # flat floor beyond the hooks so the 6 mm corner curve clears them (>= 4.2)
X0 = SOCKET_Y[0] - HOOK_W / 2 - HOOK_EDGE_MARGIN                 # 73 wide
X1 = SOCKET_Y[1] + HOOK_W / 2 + HOOK_EDGE_MARGIN
OUT_W = X1 - X0
Y0, Y1 = CASE_FRONT_Z, CASE_BACK_Z                             # as deep as the case
OUT_D = Y1 - Y0

def rrect(x0, y0, x1, y1, r):
    return sbox(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, join_style=1)

def profile(x0, z0, x1, z1, r, plinth=0.0):
    """Front-face outline: all four corners rounded. With plinth > 0 a flat plate of that height is
    kept under the curve, so the hooks at the very edges have something to attach to (the AirGradient
    stand does the same under the case)."""
    p = rrect(x0, z0, x1, z1, r)
    return p.union(sbox(x0, z0, x1, z0 + plinth)) if plinth > 0 else p

def extrude(poly, z0, z1):
    m = trimesh.creation.extrude_polygon(poly, z1 - z0)
    m.apply_translation([0, 0, z0])
    return m

def extrude_y(poly_xz, y0, y1):
    """Extrude an (X, Z) polygon along Y."""
    m = trimesh.creation.extrude_polygon(poly_xz, y1 - y0)
    v = m.vertices
    return trimesh.Trimesh(np.c_[v[:, 0], v[:, 2] + y0, v[:, 1]], m.faces[:, ::-1])

def union(a, b):  return trimesh.boolean.union([a, b], engine="manifold")
def diff(a, b):   return trimesh.boolean.difference([a, b], engine="manifold")

def cyl_y(r, y0, y1, x, z, n=64):
    c = trimesh.creation.cylinder(radius=r, height=y1 - y0, sections=n)
    c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    c.apply_translation([x, (y0 + y1) / 2, z])
    return c

_STAND = {}
def tongue_from_stand(stand_path, socket_y):
    """A true 3D copy of the stand's tongue (with its taper and chamfers), moved to a top socket.
    Case (x,y,z) -> box (X,Y,Z) = (y, z, -65.6 - x)."""
    if "mesh" not in _STAND:
        st = trimesh.load(stand_path)
        if not st.is_volume:
            trimesh.repair.fix_normals(st); trimesh.repair.fix_winding(st); st.merge_vertices()
        region = trimesh.creation.box(extents=[15.9, 5.5, 18.6])          # x -65.9..-50, y around the socket, z 2..20.6
        region.apply_translation([-65.9 + 15.9 / 2, -112.5, 2.0 + 18.6 / 2])
        t = trimesh.boolean.intersection([st, region], engine="manifold")
        M = np.array([[0, 1, 0, 0], [0, 0, 1, 0], [-1, 0, 0, -65.6], [0, 0, 0, 1]], float)   # reflection; trimesh flips faces
        t.apply_transform(M)
        # shave the head's top so the gap under the floor is LIP_T + clearance (head bottom and reach stay)
        g = LIP_T + HOOK_GAP_CLEAR
        cut1 = trimesh.creation.box(extents=[20, 200, g - 0.01])           # Y < 10: full gap height
        cut1.apply_translation([-112.5, 10.0 - 100, -g / 2 - 0.005])
        cut2 = trimesh.creation.box(extents=[20, 200, g - LIP_T + 0.05])  # Y < 13.2: only the thin strip, keeps the ramp
        cut2.apply_translation([-112.5, 13.2 - 100, -(g + LIP_T - 0.05) / 2])
        t = trimesh.boolean.difference([t, cut1], engine="manifold")
        t = trimesh.boolean.difference([t, cut2], engine="manifold")
        _STAND["mesh"] = t
    m = _STAND["mesh"].copy()
    m.apply_translation([socket_y - (-112.5), 0, 0])
    return m

def main(stand_path):
    outer = profile(X0, 0, X1, OUT_H, CORNER_R)
    inner = profile(X0 + WALL, FLOOR, X1 - WALL, OUT_H - WALL, CORNER_R - WALL)
    body = diff(extrude_y(outer, Y0, Y1), extrude_y(inner, Y0 - 1, Y1 - WALL))   # open at the front

    # CO board on the back wall, left, plug facing right (board rotated 180 deg)
    bcx = X0 + WALL + MARGIN + BOARD_W / 2
    bcz = (FLOOR + OUT_H - WALL) / 2          # both boards centred in the cavity
    y_back = Y1 - WALL
    for sx in (-1, 1):
        for sz in (-1, 1):
            cx, cz = bcx + sx * HOLE_DX / 2, bcz + sz * HOLE_DZ / 2
            body = union(body, cyl_y(STANDOFF_D / 2, y_back - STANDOFF_H, y_back + WALL / 2, cx, cz))
            body = diff(body, cyl_y(SCREW_D / 2, y_back - STANDOFF_H - 0.5, y_back - STANDOFF_H + 4.5, cx, cz, 32))
    cell_front_y = y_back - STANDOFF_H - 1.6 - CELL_H

    # floor openings exactly over the case's vent slots; the two cables go through them
    for (ya, yb) in CASE_VENTS_BETWEEN_SOCKETS:
        body = diff(body, extrude(rrect(ya, VENT_Z[0], yb, VENT_Z[1], 1.9), -1, FLOOR + 1))

    # two vent slots in the top, same size and positions as the floor openings
    ymid = (Y0 + Y1) / 2
    for (ya, yb) in CASE_VENTS_BETWEEN_SOCKETS:
        body = diff(body, extrude(rrect(ya, ymid - 2, yb, ymid + 2, 1.9), OUT_H - WALL - 1, OUT_H + 1))

    # hooks under the floor; each hook's outer side continues straight up until it meets the
    # corner curve (a ~0.6 mm step), so the hook grows out of solid material
    for sy in SOCKET_Y:
        hook = tongue_from_stand(stand_path, sy)
        hb = hook.bounds
        fill = extrude(sbox(hb[0][0], hb[0][1], hb[1][0], Y1), -0.01, FLOOR)
        body = union(body, union(hook, fill))

    # front plate: outer profile, inner lip, CO cell opening, buzzer posts + opening
    plate = extrude_y(outer, Y0, Y0 + PLATE_T)
    lip_out = profile(X0 + WALL + CLEAR, FLOOR + CLEAR, X1 - WALL - CLEAR, OUT_H - WALL - CLEAR, CORNER_R - WALL)
    lip_in = profile(X0 + WALL + CLEAR + 1.2, FLOOR + CLEAR + 1.2, X1 - WALL - CLEAR - 1.2, OUT_H - WALL - CLEAR - 1.2, max(CORNER_R - WALL - 1.2, 0.5))
    plate = union(plate, extrude_y(Polygon(lip_out.exterior.coords, [lip_in.exterior.coords]), Y0 + PLATE_T, Y0 + PLATE_T + PLATE_LIP))
    plate = diff(plate, cyl_y(CELL_D / 2 + CELL_OPEN_CLEAR / 2, Y0 - 1, Y0 + PLATE_T + 1, bcx, bcz, 96))
    bzx1 = X1 - WALL - MARGIN
    bzcz = bcz
    y_plate = Y0 + PLATE_T
    for sz in (-1, 1):
        cx, cz = bzx1 - BUZZ_HOLE_IN, bzcz + sz * BUZZ_HOLE_DZ / 2
        plate = union(plate, cyl_y(STANDOFF_D / 2, y_plate - PLATE_T / 2, y_plate + BUZZ_POST_H, cx, cz))
        plate = diff(plate, cyl_y(BUZZ_SCREW_D / 2, y_plate + BUZZ_POST_H - 4.5, y_plate + BUZZ_POST_H + 0.5, cx, cz, 32))
    plate = diff(plate, cyl_y(BUZZ_D / 2 + BUZZ_OPEN_CLEAR / 2, Y0 - 1, Y0 + PLATE_T + 1, bzx1 - BUZZ_CYL_IN, bzcz, 96))
    buzz_board_back_y = y_plate + BUZZ_POST_H + 1.6
    buzz_x0 = bzx1 - BUZZ_W
    cell_x1 = bcx + CELL_D / 2

    out = "docs/3d/"
    body.export(out + "co_sensor_box_body.stl")
    plate.export(out + "co_sensor_box_front.stl")
    for n, m in (("body", body), ("front plate", plate)):
        print(n, "watertight", m.is_watertight, "size", np.round(m.extents, 1), "volume cm3", round(m.volume / 1000, 1))
    print("CO cell front at Y=%.1f, buzzer board back at Y=%.1f -> clearance %.1f mm (cell/board X overlap %.1f mm)"
          % (cell_front_y, buzz_board_back_y, cell_front_y - buzz_board_back_y, max(0.0, cell_x1 - buzz_x0)))

if __name__ == "__main__":
    main(sys.argv[1])
