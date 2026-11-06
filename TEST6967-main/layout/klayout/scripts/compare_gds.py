# SPDX-License-Identifier: Apache-2.0
"""Compare two GDS files: layer by layer XOR over the flattened top cell, all text labels, subcell names and bounding
box. The top cell names may differ. Exit code 0 only if everything matches.

    python compare_gds.py <a.gds> <b.gds>
"""
import sys

import klayout.db as db


def read(path):
    ly = db.Layout()
    ly.read(path)
    tops = ly.top_cells()
    assert len(tops) == 1, "%s: %d top cells" % (path, len(tops))
    return ly, tops[0]


def layers(ly):
    return {(ly.get_info(li).layer, ly.get_info(li).datatype): li for li in ly.layer_indexes()}


def texts(ly, top):
    out = []
    for li in ly.layer_indexes():
        i = ly.get_info(li)
        it = top.begin_shapes_rec(li)
        while not it.at_end():
            s = it.shape()
            if s.is_text():
                t = s.text.transformed(it.trans())
                out.append((i.layer, i.datatype, t.string, t.x, t.y))
            it.next()
    return sorted(out)


def main():
    (la, ta), (lb, tb) = read(sys.argv[1]), read(sys.argv[2])
    bad = 0
    if ta.bbox() != tb.bbox():
        print("bounding box differs:", ta.bbox(), tb.bbox())
        bad += 1
    ma, mb = layers(la), layers(lb)
    if set(ma) != set(mb):
        print("layer list differs:", sorted(set(ma) ^ set(mb)))
        bad += 1
    n = 0
    for ld in sorted(set(ma) & set(mb)):
        ra = db.Region(ta.begin_shapes_rec(ma[ld]))
        rb = db.Region(tb.begin_shapes_rec(mb[ld]))
        x = ra ^ rb
        n += 1
        if not x.is_empty():
            print("layer %d/%d: XOR %d polygons, %.3f um2" % (ld[0], ld[1], x.count(), x.area() * la.dbu ** 2))
            bad += 1
    xa, xb = texts(la, ta), texts(lb, tb)
    if xa != xb:
        print("labels differ:", sorted(set(xa) ^ set(xb))[:10])
        bad += 1
    ca = sorted(c.name for c in la.each_cell() if c.cell_index() != ta.cell_index())
    cb = sorted(c.name for c in lb.each_cell() if c.cell_index() != tb.cell_index())
    if ca != cb:
        print("subcells differ:", ca, cb)
        bad += 1
    print("top cells %s / %s, %d layers compared by XOR, %d labels, %d subcells: %s" % (
        ta.name, tb.name, n, len(xa), len(ca), "IDENTICAL" if not bad else "%d DIFFERENCES" % bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
