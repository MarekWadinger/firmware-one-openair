"""
3D-printable box for the DFRobot SEN0466 CO sensor, clipping onto the top edge
of the AirGradient ONE (I-9PSL V9) case the same way the official stand clips
onto the bottom: two hooks into the case's sockets. The tongue geometry is
cut straight out of AirGradient's stand STL, so the fit is the same.

Usage:  .venv/bin/python docs/3d/co_sensor_box.py <path to airgradient-stand-stl.stl>
Output: docs/3d/co_sensor_box_body.stl, docs/3d/co_sensor_box_lid.stl

Box frame: X = across the case (viewer's left is -X), Y = case depth (front is -Y),
Z = up from the case's top face.
"""
import sys
import numpy as np
import trimesh
from shapely.geometry import box as sbox, Polygon
from shapely.affinity import translate

# ---- tunables (mm) --------------------------------------------------------
CELL_H = 22.0      # height of the black electrochemical cell above the board. MEASURE IT.
WALL = 1.6
FLOOR = 2.0
LID_T = 2.0
LID_LIP = 3.0
CLEAR = 0.2        # lid lip clearance
BOARD_W, BOARD_D = 37.0, 32.0     # DFRobot board (from its dimension drawing)
HOLE_DX, HOLE_DY = 30.0, 25.0     # mounting-hole grid
STANDOFF_H, STANDOFF_D, SCREW_D = 4.0, 6.0, 2.6   # M3 self-tapping into 2.6 mm
PLUG_ROOM = 9.0    # space on the left of the board for the Gravity plug + cable bend
CORNER_R = 6.0     # box corner radius (the case uses 13 on a 131 mm square)

# ---- from the case STL (case coordinates) ---------------------------------
CASE_TOP_X = 65.6                 # top face plane
SOCKET_Y = (-112.5, -52.5)        # the two socket centres (left, right)
CASE_FRONT_Z, CASE_BACK_Z = -15.6, 20.6
VENTS_Y = [(-139, -121), (-115, -97), (-91, -73), (-67, -49)]   # top-face vent slots
VENT_Z = (-2.0, 2.0)

# ---- derived --------------------------------------------------------------
OUT_W = 70.0                                      # spans both sockets; board + plug need only 48
OUT_D = BOARD_D + 2 * WALL + 1.0                  # 36.2 = case depth
IN_H = STANDOFF_H + 1.6 + CELL_H + 2.0
OUT_H = FLOOR + IN_H
X0 = (SOCKET_Y[0] + SOCKET_Y[1]) / 2 - OUT_W / 2  # centred on the case
X1 = X0 + OUT_W
Y0 = CASE_FRONT_Z - (OUT_D - (CASE_BACK_Z - CASE_FRONT_Z)) / 2   # centre the box on the case depth
Y1 = Y0 + OUT_D

def rrect(x0, y0, x1, y1, r):
    return sbox(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, join_style=1)

def extrude(poly, z0, z1):
    m = trimesh.creation.extrude_polygon(poly, z1 - z0)
    m.apply_translation([0, 0, z0])
    return m

def union(a, b):  return trimesh.boolean.union([a, b], engine="manifold")
def diff(a, b):   return trimesh.boolean.difference([a, b], engine="manifold")

def tongue_from_stand(stand_path, socket_y):
    """The stand's hook profile (x-z section through the stand at its socket), extruded 4 mm,
    moved to a top socket. Case (x,y,z) -> box (X,Y,Z) = (y, z, -65.6 - x)."""
    from shapely.geometry import box as sb
    from shapely.ops import unary_union
    st = trimesh.load(stand_path)
    sec = st.section(plane_origin=[0, -112.5, 0], plane_normal=[0, 1, 0])
    p2, T = sec.to_2D()
    polys = [pg for pg in p2.polygons_full]
    # p2 coordinates are the section plane's own frame; recover case x,z via T
    def to_case(pts2):
        pts3 = np.c_[pts2, np.zeros(len(pts2)), np.ones(len(pts2))] @ T.T
        return pts3[:, [0, 2]]
    shapes = []
    for pg in polys:
        ext = to_case(np.array(pg.exterior.coords))
        shapes.append(Polygon(ext, [to_case(np.array(i.coords)) for i in pg.interiors]))
    prof = unary_union(shapes).intersection(sb(-65.6 - 0.3, 2.0, -50, Y1))   # hook + the block filling the case's rear recess, cut flush with the box's back
    if prof.geom_type != "Polygon":
        prof = max(prof.geoms, key=lambda g: g.area)
    # profile in (Y, Z) = (z, -65.6 - x)
    yz = Polygon([(z, -65.6 - x) for x, z in prof.exterior.coords])
    m = trimesh.creation.extrude_polygon(yz, 4.0)           # local (u, v, w) = (Y, Z, X-thickness)
    v = m.vertices
    m = trimesh.Trimesh(np.c_[v[:, 2] + socket_y - 2.0, v[:, 0], v[:, 1]], m.faces)  # cyclic permutation, no flip
    if not m.is_volume:
        m.fix_normals()
    return m

def main(stand_path):
    # body: rounded box minus cavity
    body = extrude(rrect(X0, Y0, X1, Y1, CORNER_R), 0, OUT_H)
    cavity = extrude(rrect(X0 + WALL, Y0 + WALL, X1 - WALL, Y1 - WALL, CORNER_R - WALL), FLOOR, OUT_H + 1)
    body = diff(body, cavity)

    # board sits on the right, plug room on the left
    bx1 = X1 - WALL - 0.5
    bx0 = bx1 - BOARD_W
    bcx, bcy = (bx0 + bx1) / 2, (Y0 + Y1) / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = bcx + sx * HOLE_DX / 2, bcy + sy * HOLE_DY / 2
            post = trimesh.creation.cylinder(radius=STANDOFF_D / 2, height=STANDOFF_H + FLOOR, sections=48)
            post.apply_translation([cx, cy, (STANDOFF_H + FLOOR) / 2])
            body = union(body, post)
            hole = trimesh.creation.cylinder(radius=SCREW_D / 2, height=STANDOFF_H + 1, sections=32)
            hole.apply_translation([cx, cy, FLOOR + (STANDOFF_H + 1) / 2 + 0.5])
            body = diff(body, hole)

    # floor slots over the case's own vents, same size, so the case still breathes
    for (ya, yb) in VENTS_Y:
        ya, yb = max(ya, X0 + WALL + 1), min(yb, X1 - WALL - 1)
        if yb - ya > 6:
            slot = rrect(ya, VENT_Z[0], yb, VENT_Z[1], 1.9)
            body = diff(body, extrude(slot, -1, FLOOR + 1))

    # cable notch: rear wall, left end, at floor level. The Gravity plug faces left, the cable
    # runs along the left wall to the back and down the case's recessed rear.
    notch = extrude(sbox(X0 + WALL + 1, Y1 - WALL - 1, X0 + WALL + 9, Y1 + 1), FLOOR, FLOOR + 5)
    body = diff(body, notch)

    # side vents: 3 slots low on front and back walls (cross-flow for the sensor)
    for xw in np.linspace(bx0 + 4, bx1 - 4, 3):
        for yw in (Y0, Y1 - WALL):
            v = trimesh.creation.box(extents=[12, WALL + 2, 3])
            v.apply_translation([xw, yw + WALL / 2, FLOOR + 5])
            body = diff(body, v)

    # the two hooks, straight under the floor
    for sy in SOCKET_Y:
        body = union(body, tongue_from_stand(stand_path, sy))

    # lid: plate + inner lip with clearance, vent slots in the case's style
    lid = extrude(rrect(X0, Y0, X1, Y1, CORNER_R), 0, LID_T)
    lip_out = rrect(X0 + WALL + CLEAR, Y0 + WALL + CLEAR, X1 - WALL - CLEAR, Y1 - WALL - CLEAR, CORNER_R - WALL)
    lip_in = rrect(X0 + WALL + CLEAR + 1.2, Y0 + WALL + CLEAR + 1.2, X1 - WALL - CLEAR - 1.2, Y1 - WALL - CLEAR - 1.2, max(CORNER_R - WALL - 1.2, 0.5))
    lid = union(lid, extrude(Polygon(lip_out.exterior.coords, [lip_in.exterior.coords]), LID_T, LID_T + LID_LIP))
    for i in range(5):
        cx = X0 + OUT_W / 2 + (i - 2) * 12.0
        lid = diff(lid, extrude(rrect(cx - 2, bcy - 10, cx + 2, bcy + 10, 1.9), -1, LID_T + 1))

    out = "docs/3d/"
    body.export(out + "co_sensor_box_body.stl")
    lid.export(out + "co_sensor_box_lid.stl")
    for n, m in (("body", body), ("lid", lid)):
        print(n, "watertight", m.is_watertight, "size", np.round(m.extents, 1), "volume cm3", round(m.volume / 1000, 1))

if __name__ == "__main__":
    main(sys.argv[1])
