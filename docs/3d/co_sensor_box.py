"""
3D-printable box for the DFRobot SEN0466 CO sensor, clipping onto the top edge
of the AirGradient ONE (I-9PSL V9) case the same way the official stand clips
onto the bottom: two hooks into the case's sockets. The tongue geometry is
cut straight out of AirGradient's stand STL, so the fit is the same.

Usage:  .venv/bin/python docs/3d/co_sensor_box.py <path to airgradient-stand-stl.stl>
Output: docs/3d/co_sensor_box_body.stl, docs/3d/co_sensor_box_lid.stl

Box frame: X = across the case (viewer's left is -X), Y = case depth (front is -Y),
Z = up from the case's top face. v2: the sensor stands against the back wall, cell facing
forward through a round opening in the front; box depth equals the case depth.
"""
import sys
import numpy as np
import trimesh
from shapely.geometry import box as sbox, Polygon
from shapely.affinity import translate

# ---- tunables (mm) --------------------------------------------------------
CELL_H = 22.0      # height of the black electrochemical cell above the board. MEASURE IT.
CELL_D = 21.0      # diameter of the cell. MEASURE IT.
WALL = 1.6
FLOOR = 2.0
LID_T = 2.0
LID_LIP = 3.0
CLEAR = 0.2        # lid lip clearance
BOARD_W, BOARD_H = 37.0, 32.0     # DFRobot board, standing: 37 across (X), 32 tall (Z)
HOLE_DX, HOLE_DZ = 30.0, 25.0     # mounting-hole grid
STANDOFF_H, STANDOFF_D, SCREW_D = 4.0, 6.0, 2.6   # posts on the back wall, M3 self-tapping into 2.6 mm
OUT_W = 70.0       # spans both sockets
CORNER_R = 6.0

# ---- from the case STL (case coordinates) ---------------------------------
SOCKET_Y = (-112.5, -52.5)        # the two socket centres, 60 mm apart, same top and bottom
CASE_FRONT_Z, CASE_BACK_Z = -15.6, 20.6
CASE_VENTS_BETWEEN_SOCKETS = [(-108.0, -87.0), (-78.0, -57.0)]   # the two top-face openings between the sockets
VENT_Z = (-2.0, 2.0)

# ---- derived --------------------------------------------------------------
OUT_D = CASE_BACK_Z - CASE_FRONT_Z                # 36.2: as thick as the case
IN_H = BOARD_H + 1.0 + LID_LIP                    # board + clearance + room for the lid lip
OUT_H = FLOOR + IN_H
X0 = (SOCKET_Y[0] + SOCKET_Y[1]) / 2 - OUT_W / 2  # centred on the case
X1 = X0 + OUT_W
Y0, Y1 = CASE_FRONT_Z, CASE_BACK_Z                # flush with the case front and back

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
    body = extrude(rrect(X0, Y0, X1, Y1, CORNER_R), 0, OUT_H)
    cavity = extrude(rrect(X0 + WALL, Y0 + WALL, X1 - WALL, Y1 - WALL, CORNER_R - WALL), FLOOR, OUT_H + 1)
    body = diff(body, cavity)

    # board stands against the back wall, centred in X, cell facing the front
    bcx = (X0 + X1) / 2
    bcz = FLOOR + 0.5 + BOARD_H / 2
    y_wall = Y1 - WALL                              # inner face of the back wall
    for sx in (-1, 1):
        for sz in (-1, 1):
            cx, cz = bcx + sx * HOLE_DX / 2, bcz + sz * HOLE_DZ / 2
            post = trimesh.creation.cylinder(radius=STANDOFF_D / 2, height=STANDOFF_H + WALL, sections=48)
            post.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))   # axis along Y
            post.apply_translation([cx, y_wall - STANDOFF_H / 2 + WALL / 2, cz])
            body = union(body, post)
            hole = trimesh.creation.cylinder(radius=SCREW_D / 2, height=STANDOFF_H + 1.0, sections=32)
            hole.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
            hole.apply_translation([cx, y_wall - STANDOFF_H / 2 + 0.5, cz])
            body = diff(body, hole)

    # round opening in the front wall for the cell
    op = trimesh.creation.cylinder(radius=CELL_D / 2 + 1.0, height=WALL + 2, sections=96)
    op.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    op.apply_translation([bcx, Y0 + WALL / 2, bcz])
    body = diff(body, op)

    # floor openings exactly over the case's two vent slots between the sockets
    for (ya, yb) in CASE_VENTS_BETWEEN_SOCKETS:
        body = diff(body, extrude(rrect(ya, VENT_Z[0], yb, VENT_Z[1], 1.9), -1, FLOOR + 1))

    # cable notch: back wall, left end, at floor level (Gravity plug faces left)
    notch = extrude(sbox(X0 + WALL + 1, Y1 - WALL - 1, X0 + WALL + 9, Y1 + 1), FLOOR, FLOOR + 5)
    body = diff(body, notch)

    # the two hooks, straight under the floor
    for sy in SOCKET_Y:
        body = union(body, tongue_from_stand(stand_path, sy))

    # lid: plate + inner lip, vent slots in the case's style
    lid = extrude(rrect(X0, Y0, X1, Y1, CORNER_R), 0, LID_T)
    lip_out = rrect(X0 + WALL + CLEAR, Y0 + WALL + CLEAR, X1 - WALL - CLEAR, Y1 - WALL - CLEAR, CORNER_R - WALL)
    lip_in = rrect(X0 + WALL + CLEAR + 1.2, Y0 + WALL + CLEAR + 1.2, X1 - WALL - CLEAR - 1.2, Y1 - WALL - CLEAR - 1.2, max(CORNER_R - WALL - 1.2, 0.5))
    lid = union(lid, extrude(Polygon(lip_out.exterior.coords, [lip_in.exterior.coords]), LID_T, LID_T + LID_LIP))
    lcy = (Y0 + Y1) / 2
    for i in range(5):
        cx = bcx + (i - 2) * 12.0
        lid = diff(lid, extrude(rrect(cx - 2, lcy - 10, cx + 2, lcy + 10, 1.9), -1, LID_T + 1))

    out = "docs/3d/"
    body.export(out + "co_sensor_box_body.stl")
    lid.export(out + "co_sensor_box_lid.stl")
    for n, m in (("body", body), ("lid", lid)):
        print(n, "watertight", m.is_watertight, "size", np.round(m.extents, 1), "volume cm3", round(m.volume / 1000, 1))

if __name__ == "__main__":
    main(sys.argv[1])
