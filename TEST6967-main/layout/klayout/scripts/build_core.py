# SPDX-License-Identifier: Apache-2.0
"""Layout generator of TEST6967 (IHP SG13CMOS5L): writes the core GDS, before seal ring and PDK filler.

Layout: RF_PROBE, a GSG probe pad at mid height, feeds a 6-um TopMetal1 line over Metal1 ground (about 50 ohm). The
line runs in +x to a T junction, where a short-circuited stub continues in +x. Two vertical branches lead up and down
to the height of the two RF pads RF_BOND_A and RF_BOND_B at the right chip edge. Each horizontal branch has one
short-circuited stub pointing towards the chip centre, followed by a series line to its RF pad. CAL_OPEN and CAL_SHORT
are probe-pad de-embedding structures in the ground plate: same GSG geometry and ground window as RF_PROBE, probed from
the left, with the reference plane at the window edge. PROBE_TEST between them is a further SHORT for probe landing and
contact tests, so that the two standards are not touched more often than necessary. LAND_A and LAND_B at the left chip
edge are floating pads, the mirror image of the RF pads in x, as landing pads for wires from a neighbouring chip.

    python build_core.py --name TEST6967 --x 1000 --y 1000 --network 65 70 65 60 --t_stub 160 \\
        --gnd_pad 510 895 --gnd_sym --bond_pad 70 --cal 430 300 700 --probe_test 500 --land_pads 792 208 --plate_x 345

--network L_S L_P L_H L_F (um)
    L_S: series line, stub centre minus W/2 to the RF pad edge
    L_P: stub length from the line edge to the short circuit
    L_H: vertical branch centre to stub centre
    L_F: RF_PROBE signal pad edge to the vertical branch edge

Writes <name>_core.gds. scripts/seal_fill.sh adds the seal ring and the PDK filler.
"""
import argparse
import math
import os

import klayout.db as db

EDGE = 40.0                 # no drawn metal closer to the die edge (seal ring)
PAD = 60.0                  # pad metal, x size
PAD_OPENING = 55.0          # passivation opening of the RF pads and their ground pads
PAD_FROM_EDGE = 99.18       # centre of the RF pads and minimum centre of RF_PROBE, from the die edge
PITCH = 100.0               # GSG pitch
WINDOW_GAP = 20.0           # ground window around the signal pads, in x
BOND_GND_CLEAR = 40.0       # ground window around the RF pads, in y
CORRIDOR = 30.0             # solid Metal1 ground beyond the line edge
GRID_GAP = 2.0              # Metal1 gap between the corridor and the grid
PAD_EXIT = 8.0              # Pad.eR/Pad.fR: metal at a pad at least 7 um wide and long, slits and edges 8 um away
STACK, STACK_PITCH = 6.0, 20.0
PLATE_INSET = EDGE + 15.0   # outer edge of the TopMetal1 plate, keeps TM1 below the density limit (TM1.d) and Pad.dR
SEAL_CORNER = 60.0          # no Metal1 grid in the die corners up to this distance from the die edges

M1, V1, M2, V2, M3, V3, M4, TV1, TM1, PASSIV, DFPAD = 8, 19, 10, 29, 30, 49, 50, 125, 126, 9, 41
PR_BOUNDARY = 189
DRAW, FILL, NOFILL, SLIT, TEXT = 0, 22, 23, 24, 25
VIAS = {V1: (0.19, 0.48, 0.6), V2: (0.19, 0.48, 0.6), V3: (0.19, 0.48, 0.6), TV1: (0.42, 0.84, 0.8)}   # size, pitch, enclosure
STACK_METALS = (M2, M3, M4)
FILL_METALS = (M2, M3, M4)
NOFILL_METALS = (M1, M2, M3, M4)
W, CHANNEL = 6.0, 15.0      # line width and gap to the plate; TM1 over M1, h = 3.94 um


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=".", help="output directory")
    ap.add_argument("--name", default="TEST6967")
    ap.add_argument("--x", type=float, default=1000.0)
    ap.add_argument("--y", type=float, default=1000.0)
    ap.add_argument("--network", type=float, nargs=4, metavar=("L_S", "L_P", "L_H", "L_F"), required=True)
    ap.add_argument("--dy", type=float, default=292.0, help="RF pads at chip centre +- DY")
    ap.add_argument("--cal", type=float, nargs=3, metavar=("X", "Y_OPEN", "Y_SHORT"), required=True,
                    help="de-embedding structures: OPEN (signal pad alone in the window), SHORT (signal pad tied to the "
                         "plate by a line across the window gap)")
    ap.add_argument("--probe_test", type=float, metavar="Y",
                    help="PROBE_TEST: one more signal pad at the x of --cal, tied to the plate like SHORT, for probe landing "
                         "and contact tests. Its ground pads are those of OPEN and SHORT at Y +- pitch")
    ap.add_argument("--land_pads", type=float, nargs="+", default=[], metavar="Y",
                    help="floating landing pads in the empty strip left of the plate, mirror image of the RF pads in x")
    ap.add_argument("--t_stub", type=float, required=True,
                    help="short-circuited stub at the T junction in +x, length from the vertical branch edge")
    ap.add_argument("--bond_pad", type=float, default=PAD,
                    help="edge length of the two RF signal pads (TM1 only), grows towards the chip centre")
    ap.add_argument("--gnd_pad", type=float, nargs=2, metavar=("X", "Y"), required=True, help="DC ground pad, 80 x 80 um")
    ap.add_argument("--gnd_sym", action="store_true", help="second DC ground pad mirrored at the chip centre")
    ap.add_argument("--plate_x", type=float, required=True,
                    help="TopMetal1 plate starts at this x, Metal1 ground 15 um further left")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    CX, CY = a.x, a.y
    XB = CX - PAD_FROM_EDGE
    YS = CY / 2                                                     # RF_PROBE and T junction
    Y_PADS = (YS + a.dy, YS - a.dy)                                 # RF_BOND_A (top), RF_BOND_B (bottom)
    h = PAD / 2
    hpx, hpy = 30.0, 20.0                                           # half size of the probe signal pad
    hg = 40.0                                                       # half height of the probe ground pads
    l_s, l_p, l_h, l_f = a.network
    hb = a.bond_pad / 2
    x_e = XB + h - 2 * hb                                           # inner edge of the RF signal pad
    x_st = x_e - l_s - W / 2                                        # centre of the branch stubs
    x_t = x_st - l_h                                                # centre of the vertical branch (T junction)
    XP = x_t - W / 2 - l_f - hpx                                    # RF_PROBE
    assert XP >= PAD_FROM_EDGE - 1e-6, "feed line too long"

    ly = db.Layout()
    ly.dbu = 0.001
    top = ly.create_cell(a.name)

    def um(v):
        return int(round(v / ly.dbu))

    def box(x0, y0, x1, y1):
        return db.Box(um(min(x0, x1)), um(min(y0, y1)), um(max(x0, x1)), um(max(y0, y1)))

    def R(*b):
        return db.Region(box(*b))

    reg = {}

    def add(lay, dt, r):
        reg[(lay, dt)] = (reg.get((lay, dt), db.Region()) + r).merged()

    # ---------------------------------------------------------------- lines (TopMetal1)
    s_probe = R(XP - hpx, YS - hpy, XP + hpx, YS + hpy)
    s_bond = db.Region()
    for yb in Y_PADS:
        s_bond += R(x_e, yb - hb, XB + h, yb + hb)
    s_land = db.Region()
    for yl in a.land_pads:
        s_land += R(CX - (XB + h), yl - hb, CX - x_e, yl + hb)
    x_a = XP + hpx
    segments = [(R(x_a, YS - W / 2, x_t + W / 2, YS + W / 2), "x"),                       # feed line
                (R(x_t - W / 2, Y_PADS[1] - W / 2, x_t + W / 2, Y_PADS[0] + W / 2), "y")]  # vertical branches
    stubs = []                                                      # (y of the short, direction away from the line)
    for yb, sgn in ((Y_PADS[0], -1), (Y_PADS[1], +1)):
        segments.append((R(x_t - W / 2, yb - W / 2, x_e, yb + W / 2), "x"))
        y0 = yb + sgn * W / 2
        y_short = y0 + sgn * l_p                                    # stub end = plate edge
        segments.append((R(x_st - W / 2, min(y0, y_short), x_st + W / 2, max(y0, y_short)), "y"))
        stubs.append((y_short, sgn))
    assert abs(stubs[0][0] - YS) > 2 * (CHANNEL + STACK + 10), "branch stubs meet at the centre"
    t_short = x_t + W / 2 + a.t_stub                                # stub end = plate edge
    segments.append((R(x_t + W / 2, YS - W / 2, t_short, YS + W / 2), "x"))
    assert (t_short < x_st - W / 2 - 2 * CHANNEL - 2 * STACK
            or min(abs(yk - YS) for yk, _ in stubs) > W + 2 * (CHANNEL + 1.0 + STACK) + 4.0), "T stub hits the branch stubs"
    assert t_short < CX - EDGE - 15.0 - 40.0, "T stub too long"
    assert l_h - W >= 2 * (CHANNEL + 1.0 + STACK) + 4.0, "branch stub too close to the vertical branch"

    # De-embedding structures: window, signal pad and ground pads as at RF_PROBE. SHORT: line of width W across the
    # window gap to the plate, channel closed behind it. No via stack there: only the Metal1 grid lies in the window,
    # and the plate is already ground.
    xc, y_op, y_sh = a.cal
    cal_s, cal_windows, cal_text = [], [], []
    for yc in (y_op, y_sh):
        cal_s.append(R(xc - hpx, yc - hpy, xc + hpx, yc + hpy))
        cal_windows.append(R(xc - hpx - WINDOW_GAP, yc - (PITCH - hg - PAD_EXIT), xc + hpx + WINDOW_GAP,
                             yc + (PITCH - hg - PAD_EXIT)))
    segments.append((R(xc + hpx, y_sh - W / 2, xc + hpx + WINDOW_GAP, y_sh + W / 2), "x"))
    cal_shorts = [(xc + hpx + WINDOW_GAP, y_sh, +1)]
    cal_text += [("CAL_OPEN", xc, y_op + 30), ("CAL_SHORT", xc, y_sh + 30)]
    cal_g = [R(xs - h, ys + d - hg, xs + h, ys + d + hg) for sp in cal_s
             for xs, ys in [(sp.bbox().center().x * ly.dbu, sp.bbox().center().y * ly.dbu)] for d in (-PITCH, PITCH)]
    if a.probe_test is not None:
        # PROBE_TEST: same geometry as SHORT, without own ground pads
        yc = a.probe_test
        assert abs(yc - PITCH - (y_op + PITCH)) < 1e-6 and abs(yc + PITCH - (y_sh - PITCH)) < 1e-6, "PROBE_TEST needs the ground pads of OPEN and SHORT"
        cal_s.append(R(xc - hpx, yc - hpy, xc + hpx, yc + hpy))
        cal_windows.append(R(xc - hpx - WINDOW_GAP, yc - (PITCH - hg - PAD_EXIT), xc + hpx + WINDOW_GAP,
                             yc + (PITCH - hg - PAD_EXIT)))
        segments.append((R(xc + hpx, yc - W / 2, xc + hpx + WINDOW_GAP, yc + W / 2), "x"))
        cal_shorts.append((xc + hpx + WINDOW_GAP, yc, +1))
        cal_text.append(("PROBE_TEST", xc, yc + 30))
    cal_all = db.Region()
    for q in cal_windows + cal_g:
        cal_all += q
    probe_area = R(XP - hpx - WINDOW_GAP, YS - PITCH - hg, XP + hpx + WINDOW_GAP, YS + PITCH + hg)
    assert (cal_all.sized(um(15.0)) & probe_area).is_empty(), "structure closer than 15 um to the RF_PROBE GSG"

    line = db.Region()
    for r, _ in segments:
        line += r
    line.merge()
    # Pad.eR / Pad.fR: line 7 um wide on the first 8 um at a signal pad
    s_all = s_probe + s_bond
    for sp in cal_s:
        s_all += sp
    near = s_all.sized(um(8.0)) - s_all
    line = (line + ((line & near).sized(um(0.5)) & near)).merged()

    # ---------------------------------------------------------------- ground plate (TopMetal1)
    yo = hb + BOND_GND_CLEAR
    open_b = db.Region()
    for yb in Y_PADS:
        open_b += R(x_e - WINDOW_GAP, yb - yo, CX - EDGE, yb + yo)
    yo_p = PITCH - hg - PAD_EXIT
    open_p = R(XP - hpx - WINDOW_GAP, YS - yo_p, XP + hpx + WINDOW_GAP, YS + yo_p)
    channel = line.sized(um(CHANNEL))
    for xk, yk, sgn in cal_shorts:                                  # the SHORT line ends in the plate
        channel -= R(xk, yk - W / 2 - CHANNEL - 1, xk + sgn * (CHANNEL + 1.0), yk + W / 2 + CHANNEL + 1)
    for f in cal_windows:
        open_p += f
    for y_short, sgn in stubs:                                      # the branch stubs end in the plate
        channel -= R(x_st - W / 2 - CHANNEL, y_short + sgn * (CHANNEL + 1), x_st + W / 2 + CHANNEL, y_short)
    channel -= R(t_short, YS - W / 2 - CHANNEL, t_short + CHANNEL + 1, YS + W / 2 + CHANNEL)
    plate_box = R(a.plate_x, PLATE_INSET, CX - PLATE_INSET, CY - PLATE_INSET)
    m1_area = R(a.plate_x - 15.0, EDGE, CX - EDGE, CY - EDGE)
    gsg_extent = R(XP - hpx - WINDOW_GAP, YS - PITCH - 40.0, CX, YS + PITCH + 40.0)
    assert gsg_extent.bbox().left >= um(a.plate_x), "RF_PROBE GSG sticks out of the plate"
    for sp in cal_s:
        assert not (sp & plate_box.sized(um(30.0))).is_empty(), "calibration structure outside the plate"
    plate = plate_box - open_b - open_p - channel
    # Ground pads. RF side: window +-yo, the ground pads start 8 um behind it and 8 um beside the branch stub channel.
    x0_g = max(XB - h, x_st + W / 2 + CHANNEL + PAD_EXIT)
    ya, yu = Y_PADS
    g_pads = ([R(XP - h, yy - hg, XP + h, yy + hg) for yy in (YS - PITCH, YS + PITCH)]
              + [R(x0_g, ya - PITCH - h, XB + h, ya - yo - PAD_EXIT), R(XB - h, ya + yo + PAD_EXIT, XB + h, ya + PITCH + h),
                 R(XB - h, yu - PITCH - h, XB + h, yu - yo - PAD_EXIT), R(x0_g, yu + yo + PAD_EXIT, XB + h, yu + PITCH + h)]
              + cal_g)
    # at least 8 um TopMetal1 between ground pad and outer plate edge
    g_pads = [g & plate_box.sized(-um(PAD_EXIT)) for g in g_pads]
    for sp in cal_s:
        s_probe = s_probe + sp                                      # calibration signal pads are treated like RF_PROBE
    gnd_pos = [tuple(a.gnd_pad)] + ([(a.gnd_pad[0], CY - a.gnd_pad[1])] if a.gnd_sym else [])
    gnd_list = [R(gx - 40, gy - 40, gx + 40, gy + 40) for gx, gy in gnd_pos]
    gnd_dc = None
    for q in gnd_list:
        gnd_dc = q if gnd_dc is None else gnd_dc + q
    for p in g_pads + gnd_list:
        assert (p - plate).is_empty(), "ground pad not fully inside the plate"
    tm1 = (plate + line + s_probe + s_bond).merged()
    add(TM1, DRAW, tm1)

    # ---------------------------------------------------------------- Metal1 corridor below the lines
    corridor = (line.sized(um(CORRIDOR)) - open_b - open_p) & m1_area
    # no Metal1 closer than 8 um to a pad (Pad.eR_M1 / Pad.fR_M1)
    all_pads = s_probe + s_bond
    for q in g_pads + gnd_list:
        all_pads += q
    corridor -= all_pads.sized(um(PAD_EXIT))
    add(M1, DRAW, corridor)

    # ---------------------------------------------------------------- via stacks along the channel edges
    n_via = {lay: 0 for lay in VIAS}
    stacks = db.Region()

    def via_field(lay, x0, y0, x1, y1, pitch=None):
        va, p, _ = VIAS[lay]
        p = pitch or p
        nx, ny = int((x1 - x0 - va) // p) + 1, int((y1 - y0 - va) // p) + 1
        ox = round((x0 + (x1 - x0 - (va + (nx - 1) * p)) / 2) / 0.005) * 0.005
        oy = round((y0 + (y1 - y0 - (va + (ny - 1) * p)) / 2) / 0.005) * 0.005
        add(lay, DRAW, db.Region([box(ox + i * p, oy + j * p, ox + i * p + va, oy + j * p + va)
                                  for i in range(nx) for j in range(ny)]))
        n_via[lay] += nx * ny

    def via_ring(lay, x0, y0, x1, y1):
        """one row of vias along the edge of a rectangle (outer via edges on x0..x1, y0..y1)"""
        va, p, _ = VIAS[lay]
        q = []
        for u0, u1, fixed, horizontal in ((x0, x1, y0, True), (x0, x1, y1 - va, True),
                                          (y0 + p, y1 - p, x0, False), (y0 + p, y1 - p, x1 - va, False)):
            n = int((u1 - u0 - va) // p) + 1
            o = round((u0 + (u1 - u0 - (va + (n - 1) * p)) / 2) / 0.005) * 0.005
            for i in range(n):
                u = o + i * p
                q.append(box(u, fixed, u + va, fixed + va) if horizontal else box(fixed, u, fixed + va, u + va))
        add(lay, DRAW, db.Region(q))
        n_via[lay] += len(q)

    def place_stack(q):
        for lay in STACK_METALS:
            add(lay, DRAW, q)

    stack_ok = plate.sized(um(-0.5)) & corridor.sized(um(-1.5))
    stack_keepout = (s_probe + s_bond).sized(um(10.0))
    for p in g_pads:
        stack_keepout += p.sized(um(3.0))
    for r, o in segments:
        b = r.bbox()
        x0, y0, x1, y1 = b.left * ly.dbu, b.bottom * ly.dbu, b.right * ly.dbu, b.top * ly.dbu
        d = CHANNEL + 1.0
        if o == "x":
            cand = [(xx, yy) for xx in [x0 + 10.0 + i * STACK_PITCH for i in range(int((x1 - x0 - 20.0) // STACK_PITCH) + 1)]
                    for yy in (y1 + d, y0 - d - STACK)]
        else:
            cand = [(xx, yy) for yy in [y0 + 10.0 + i * STACK_PITCH for i in range(int((y1 - y0 - 20.0) // STACK_PITCH) + 1)]
                    for xx in (x1 + d, x0 - d - STACK)]
        for xx, yy in cand:
            q = R(xx, yy, xx + STACK, yy + STACK)
            if not (q - stack_ok).is_empty() or not (q & stack_keepout).is_empty() or not (q & stacks.sized(um(4.0))).is_empty():
                continue
            stacks += q
            place_stack(q)
            for lay, (_, _, enc) in VIAS.items():
                via_field(lay, xx + enc, yy + enc, xx + STACK - enc, yy + STACK - enc)
    for y_short, sgn in stubs:
        # short circuit: stack in the last piece of the branch stub, directly on the ground
        y0, y1 = sorted((y_short, y_short - sgn * STACK))
        q = R(x_st - STACK / 2, y0, x_st + STACK / 2, y1)
        assert (q - corridor).is_empty() and (q - line).is_empty()
        stacks += q
        place_stack(q)
        for lay, (_, _, enc) in VIAS.items():
            via_field(lay, x_st - STACK / 2 + enc, y0 + enc, x_st + STACK / 2 - enc, y1 - enc)
    # short circuit of the T stub
    q = R(t_short - STACK, YS - STACK / 2, t_short, YS + STACK / 2)
    stacks += q
    place_stack(q)
    b = q.bbox()
    for lay, (_, _, enc) in VIAS.items():
        via_field(lay, b.left * ly.dbu + enc, b.bottom * ly.dbu + enc, b.right * ly.dbu - enc, b.top * ly.dbu - enc)
    # via stacks plate -> Metal1 grid on a 40-um grid, away from channels, windows and pads
    # 40 um clear around all pads: the only slit column of the plate between the calibration pads stays free (Slt.c.TM1)
    grid_keepout = (channel.sized(um(3.0)) + open_p.sized(um(3.0)) + open_b.sized(um(3.0)) + all_pads.sized(um(40.0)))
    grid_ok = plate.sized(um(-1.0))
    for i in range(int((CX - 2 * EDGE) // 40.0) + 1):
        for j in range(int((CY - 2 * EDGE) // 40.0) + 1):
            xx, yy = EDGE + 17.0 + i * 40.0, EDGE + 17.0 + j * 40.0
            # not in the corners next to the seal ring chamfer (V1.c1 of the maximal deck)
            if min(xx, CX - xx) < 100.0 and min(yy, CY - yy) < 100.0:
                continue
            q = R(xx, yy, xx + STACK, yy + STACK)
            if not (q - grid_ok).is_empty() or not (q & grid_keepout).is_empty() or not (q & stacks.sized(um(4.0))).is_empty():
                continue
            stacks += q
            add(M1, DRAW, R(xx - 0.5, yy - 0.5, xx + STACK + 0.5, yy + STACK + 0.5))
            place_stack(q)
            for lay, (_, _, enc) in VIAS.items():
                via_field(lay, xx + enc, yy + enc, xx + STACK - enc, yy + STACK - enc)
    # Ground pads and DC pads: stack M2..TM1 with via fields, without M1 and Via1 (the Metal1 grid stays 8 um away,
    # Pad.fR_M1), no slits (Slt.e). TopVia1 only as a ring 1.4 um inside the pad edge, outside the passivation opening
    # (Pad.kR, Pad.gR; as in the IHP bondpad PCell).
    for q in g_pads + gnd_list:
        b = q.bbox()
        x0, y0, x1, y1 = b.left * ly.dbu, b.bottom * ly.dbu, b.right * ly.dbu, b.top * ly.dbu
        place_stack(q)
        for lay, (va, pp, enc) in VIAS.items():
            if lay == V1:
                continue
            if lay == TV1:
                via_ring(lay, x0 + 1.4, y0 + 1.4, x1 - 1.4, y1 - 1.4)
                continue
            via_field(lay, x0 + enc + 1.0, y0 + enc + 1.0, x1 - enc - 1.0, y1 - enc - 1.0, pitch=1.5)
    stacks.merge()

    # ---------------------------------------------------------------- slits
    def slit_field(allowed, sw, sl, px, py, x0, y0):
        if allowed.is_empty():
            return db.Region()
        bb = allowed.bbox()
        r = db.Region()
        i0 = math.floor((bb.left * ly.dbu - x0) / px)
        j0 = math.floor((bb.bottom * ly.dbu - y0) / py)
        for j in range(j0, j0 + int(bb.height() * ly.dbu / py) + 2):
            for i in range(i0, i0 + int(bb.width() * ly.dbu / px) + 2):
                r.insert(box(x0 + i * px, y0 + j * py, x0 + i * px + sl, y0 + j * py + sw))
        return r.select_inside(allowed)

    pads = s_probe + s_bond
    for p in g_pads + gnd_list:
        pads += p
    slit_keepout = pads.sized(um(PAD_EXIT)) + stacks.sized(um(1.5))
    tm1_slits = slit_field(plate.sized(um(-5.0)) - slit_keepout, 3.0, 20.0, 26.0, 10.0,
                           plate.bbox().left * ly.dbu + 8.0, EDGE + 6.0)

    def complete_slits(metal, slits, allowed, name):
        """Check Slt.c as the DRC deck does (metal without pads and slits, shrunk by 15 um) and break the rest, which
        the slit raster misses at pads, stacks and corners, with 3 x 20 (else 3 x 10 / 3 x 5) um slits along the long
        axis"""
        for _ in range(30):
            wide = (metal - pads - slits).sized(-um(15.0), 3)
            if wide.is_empty():
                break
            new = db.Region()
            for p in wide.each():
                b = p.bbox()
                xm, ym = b.center().x * ly.dbu, b.center().y * ly.dbu
                long_x = b.width() >= b.height()
                l0, l1 = (b.left, b.right) if long_x else (b.bottom, b.top)
                l0, l1 = l0 * ly.dbu, l1 * ly.dbu
                sites = ([(l0 + l1) / 2] if l1 - l0 < 25.0
                         else [l0 + 5.0 + k * 25.0 for k in range(int((l1 - l0 - 5.0) // 25.0) + 1)])
                n0 = new.count()
                for u in sites:
                    for sl in (20.0, 10.0, 5.0):
                        q = db.Region(box(u - sl / 2, ym - 1.5, u + sl / 2, ym + 1.5) if long_x
                                      else box(xm - 1.5, u - sl / 2, xm + 1.5, u + sl / 2))
                        if (q - allowed).is_empty() and (q & (slits + new).sized(um(2.0))).is_empty():
                            new += q
                            break
                if new.count() > n0:
                    continue
                # centre blocked (e.g. T junction, ground below the lines): nearest allowed place for a 3 x 3 um slit
                # within 14 um of the rest
                zone = db.Region(p).sized(um(14.0)) & allowed.sized(-um(1.5))
                if zone.is_empty():
                    continue
                zb = zone.bbox()
                cand = sorted(((x * 0.5, y * 0.5) for x in range(int(zb.left * ly.dbu * 2), int(zb.right * ly.dbu * 2) + 1)
                               for y in range(int(zb.bottom * ly.dbu * 2), int(zb.top * ly.dbu * 2) + 1)),
                              key=lambda c: (c[0] - xm) ** 2 + (c[1] - ym) ** 2)
                for cx, cy in cand:
                    q = db.Region(box(cx - 1.5, cy - 1.5, cx + 1.5, cy + 1.5))
                    if (q - allowed).is_empty() and (q & (slits + new).sized(um(2.0))).is_empty():
                        new += q
                        break
            if new.is_empty():
                print("### WARNING Slt.c %s: %d places without room for slits: %s" % (
                    name, wide.count(), [str(p.bbox().to_dtype(ly.dbu)) for p in wide.each()][:5]))
                break
            slits = slits + new
        return slits

    tm1_slits = complete_slits(tm1, tm1_slits, plate.sized(um(-1.5)) - slit_keepout, "TopMetal1")

    def slit_density(metal, slits, allowed, name, target=0.065):
        """Slt.i: every piece of metal that survives an opening by 35 um needs at least 6 % slit area. Blocks next to
        ground pads do not reach it with the raster: add 3 x 20 um slits row by row (2 um metal to neighbouring slits)"""
        n = 0
        for part in metal.sized(-um(17.5)).sized(um(17.5)).merged().each():
            r_t = db.Region(part)
            free_t = allowed & r_t
            if free_t.is_empty():
                continue
            bb = free_t.bbox()
            missing = target * r_t.area() - (slits & r_t).area()
            yy = bb.bottom * ly.dbu
            while missing > 0 and yy + 3.0 <= bb.top * ly.dbu:
                xx, placed = bb.left * ly.dbu, False
                while xx + 20.0 <= bb.right * ly.dbu:
                    q = db.Region(box(xx, yy, xx + 20.0, yy + 3.0))
                    if (q - free_t).is_empty() and (q & (slits & r_t.sized(um(5.0))).sized(um(2.0))).is_empty():
                        slits = slits + q
                        missing -= q.area()
                        n += 1
                        placed = True
                        xx += 26.0
                        if missing <= 0:
                            break
                    else:
                        xx += 1.0
                yy += 5.0 if placed else 0.5
            if missing > 0:
                print("### WARNING Slt.i %s: block %s stays below %.1f %%" % (name, part.bbox().to_dtype(ly.dbu), 100 * target))
        print("### Slt.i %s: %d additional slits" % (name, n))
        return slits

    tm1_slits = slit_density(tm1, tm1_slits, plate.sized(um(-1.5)) - slit_keepout, "TopMetal1")
    add(TM1, SLIT, tm1_slits)
    # Metal1 corridor: slit rows parallel to each line, 3 x 15 um on an 18-um raster, on the inside 10.5 um beside the
    # line edge, on the outside behind the via stacks if there is room (Slt.c, Slt.i); no slits below pads (Slt.e)
    m1_ok = corridor.sized(um(-1.5)) - line.sized(um(10.4)) - stacks.sized(um(1.5)) - pads.sized(um(PAD_EXIT))
    m1_slits = db.Region()
    d_outer = CHANNEL + 1.0 + STACK + 1.5
    for k_seg, (r, o) in enumerate(segments):
        b = r.bbox()
        x0, y0, x1, y1 = b.left * ly.dbu, b.bottom * ly.dbu, b.right * ly.dbu, b.top * ly.dbu
        # feed line: raster from the T junction, so that the last slit ends at the keepout of the vertical branch
        x_phase = x0 + 1.5 if k_seg else (x_t - W / 2 - 10.45 - 15.0) - 18.0 * math.floor((x_t - W / 2 - 10.45 - 15.0 - x0) / 18.0)
        for d in (10.5, d_outer):
            if d + 3.0 > CORRIDOR - 1.5:
                continue
            if o == "x":
                for yy in (y1 + d, y0 - d - 3.0):
                    new = slit_field(m1_ok & R(x0 - CORRIDOR, yy, x1 + CORRIDOR, yy + 3.0), 3.0, 15.0, 18.0, 1000.0, x_phase, yy)
                    m1_slits += new.not_interacting(m1_slits.sized(um(2.0)))    # corners: rows must not cross (Slt.a)
            else:
                for xx in (x1 + d, x0 - d - 3.0):
                    new = slit_field(m1_ok & R(xx, y0 - CORRIDOR, xx + 3.0, y1), 15.0, 3.0, 1000.0, 18.0, xx, y0 - CORRIDOR + 1.5)
                    m1_slits += new.not_interacting(m1_slits.sized(um(2.0)))
    m1_slits.merge()

    # Metal1 grid: 4-um tracks on a 12-um raster in both directions (M1.j >= 35 %), below the plate and the probe windows,
    # not below the RF pad windows; corridor and pad stacks stay solid. Metal1 is nofill there, the grid gives the density.
    grid_area = m1_area - open_b
    tracks = db.Region()
    for k in range(int((CY - 2 * EDGE) // 12.0) + 1):
        tracks.insert(box(EDGE, EDGE + 1.0 + k * 12.0, CX - EDGE, EDGE + 5.0 + k * 12.0))
    for k in range(int((CX - 2 * EDGE) // 12.0) + 1):
        tracks.insert(box(EDGE + 1.0 + k * 12.0, EDGE, EDGE + 5.0 + k * 12.0, CY - EDGE))
    # The chamfered corners of the seal ring reach into the rectangular grid area. The grid stays off them, so that the
    # Metal1 ground and the seal ring are separate polygons: Metal1 merged with the seal ring is not "outside EdgeSeal",
    # and rule V1.c1 would then find no Metal1 around any Via1 (Calibre; the KLayout deck selects raw shapes and misses it).
    corners = db.Region()
    for x0, x1 in ((0.0, SEAL_CORNER), (CX - SEAL_CORNER, CX)):
        for y0, y1 in ((0.0, SEAL_CORNER), (CY - SEAL_CORNER, CY)):
            corners += R(x0, y0, x1, y1)
    # The corridor is the only Metal1 plate wider than 35 um and holds the Metal1 slits. A gap keeps the grid out of its
    # polygon, so that a per-region slit density (Slt.i, gdscheck) sees the plate alone; corridor and grid stay connected
    # through the via stacks and the TopMetal1 plate. The narrow block below CAL_SHORT has no stacks and stays on the grid.
    # The grid in the RF_PROBE window stays on the corridor, so that no gap lies at the reference plane (window edge); the
    # gap runs around the window. Remainders below 1 um width are removed.
    solid = corridor.merged()
    solid_plate = solid.interacting(solid.sized(-um(17.5)))
    probe_window = open_p.interacting(solid_plate.sized(um(1.0)))
    grid = (tracks.merged() & grid_area) - (solid_plate + probe_window).sized(um(GRID_GAP)) - (solid - solid_plate).sized(um(-0.01))
    grid += tracks.merged() & probe_window
    grid = (grid - all_pads.sized(um(8.0)) - corners).sized(-um(0.5)).sized(um(0.5))
    add(M1, DRAW, grid)
    # A grid track can land closer to a corridor edge than M1.e allows (0.22 um). Such a gap is a notch of one polygon:
    # Calibre reports it, the KLayout deck does not. Fill gaps below 0.5 um.
    add(M1, DRAW, reg[(M1, DRAW)].sized(um(0.25)).sized(-um(0.25)))
    add(M1, NOFILL, grid_area)
    print("### Metal1 grid: %.1f %% coverage in the grid area" % (100 * (grid + corridor).merged().area() / max(grid_area.area(), 1)))
    # Slt.c over the whole Metal1 layer (corridor, grid, stacks); slits only in the corridor outside the line zone
    m1_slits = complete_slits(reg.get((M1, DRAW), db.Region()), m1_slits, m1_ok, "Metal1")
    add(M1, SLIT, m1_slits)

    # ---------------------------------------------------------------- pads, nofill, filler, boundary, text
    # Passivation opening: probe side and DC pads 2.1 um inside the pad edge, RF pad side 2.5 um
    e_probe = 2.1
    e_bond = (PAD - PAD_OPENING) / 2
    pad_list = ([(q, e_probe) for q in s_probe.each()] + [(q, e_bond) for q in s_bond.each()]
                + [(q, e_probe) for g in g_pads[:2] for q in g.each()]
                + [(q, e_bond) for g in g_pads[2:6] for q in g.each()]
                + [(q, e_probe) for g in g_pads[6:] for q in g.each()]
                + [(q, e_probe) for q in gnd_dc.each()]
                + [(q, e_bond) for q in s_land.each()])
    for q, e in pad_list:
        add(DFPAD, DRAW, db.Region(q))
        b = q.bbox()
        add(PASSIV, DRAW, R(b.left * ly.dbu + e, b.bottom * ly.dbu + e, b.right * ly.dbu - e, b.top * ly.dbu - e))
    add(TM1, DRAW, gnd_dc)
    assert (s_land.sized(um(PAD_EXIT)) & m1_area).is_empty(), "landing pad too close to the Metal1 ground"
    add(TM1, DRAW, s_land)                                          # floating, TopMetal1 only
    # RF zone without filler: windows and channels + 5 um (Metal2..4 filler above the Metal1 corridor stays at least 20 um
    # beside the lines, keeps Mn.j >= 35 %)
    rf_zone = ((open_b + open_p + channel).sized(um(5.0)) + s_land.sized(um(PAD_EXIT))) & R(EDGE, EDGE, CX - EDGE, CY - EDGE)
    for lay in NOFILL_METALS:
        add(lay, NOFILL, rf_zone)
    add(TM1, NOFILL, R(0, 0, CX, CY))
    fill_area = R(EDGE + 5, EDGE + 5, CX - EDGE - 5, CY - EDGE - 5) - rf_zone - stacks.sized(um(1.5))
    for k, lay in enumerate(FILL_METALS):
        o = EDGE + 1.0 + (3.3 if k % 2 else 0.0)
        free_l = fill_area - reg.get((lay, DRAW), db.Region()).sized(um(1.5))   # MnFil.c 0.42 um to drawn metal
        add(lay, FILL, slit_field(free_l, 5.0, 5.0, 6.6, 6.6, o, o))
    add(PR_BOUNDARY, 0, R(0, 0, CX, CY))
    for (lay, dt), r in reg.items():
        top.shapes(ly.layer(lay, dt)).insert(r)
    TX = ly.layer(TM1, TEXT)
    for xx, yc, t in ((XP, YS, "RF_PROBE"), (XB, Y_PADS[0], "RF_BOND_A"), (XB, Y_PADS[1], "RF_BOND_B")):
        top.shapes(TX).insert(db.Text(t, db.Trans(db.Vector(um(xx), um(yc)))))
        for yy in (yc - PITCH, yc + PITCH):
            top.shapes(TX).insert(db.Text("GND", db.Trans(db.Vector(um(xx), um(yy)))))
    for gx, gy in gnd_pos:
        top.shapes(TX).insert(db.Text("GND_DC", db.Trans(db.Vector(um(gx), um(gy)))))
    for t, xx, yy in cal_text:
        top.shapes(TX).insert(db.Text(t, db.Trans(db.Vector(um(xx), um(yy)))))
    for k, yl in enumerate(a.land_pads):
        top.shapes(TX).insert(db.Text("LAND_" + "ABCDEF"[k], db.Trans(db.Vector(um(CX - XB), um(yl)))))
    out = os.path.join(a.out, a.name + "_core.gds")
    opt = db.SaveLayoutOptions()
    opt.gds2_max_vertex_count = 4000                                # GDS limit 8191 points per polygon
    ly.write(out, opt)

    print("### %s: chip %.0f x %.0f um = %.3f mm2" % (os.path.basename(out), CX, CY, CX * CY / 1e6))
    print("### RF_PROBE (%.2f, %.1f), RF pads x %.2f, y %.1f / %.1f; feed line %.1f um to the T junction at x %.2f" % (
        XP, YS, XB, Y_PADS[0], Y_PADS[1], l_f, x_t))
    print("### network per branch: series line %.1f um, stub %.1f um (centre x %.2f, short at y %.2f / %.2f), "
          "T to stub %.1f um, T stub %.1f um" % (l_s, l_p, x_st, stubs[0][0], stubs[1][0], l_h, a.t_stub))
    print("### %d via stacks; vias %s; slits TM1 %d, M1 %d" % (stacks.count(), n_via, tm1_slits.count(), m1_slits.count()))


if __name__ == "__main__":
    main()
