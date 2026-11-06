# SPDX-License-Identifier: Apache-2.0
"""Release GDS for Open-Silicon-MPW from the finished chip GDS:
  - sets the top cell name (must equal the IP name)
  - corrects the area label of the seal ring PCell ("1.0e-06 sq mm" -> "1.0 sq mm")
  - saves with the KLayout options of Open-Silicon-MPW (fig/klayout_save.png): no PCell context, zero-length paths
    eliminated, max. 8000 vertices, library name LIB, database unit 0.001 um
  - proves by XOR that the geometry of each layer is unchanged and that the labels are unchanged except the area label

    python make_release.py <in.gds> <out.gds> <name>
"""
import hashlib
import re
import sys

import klayout.db as db


def read(path):
    ly = db.Layout()
    ly.read(path)
    return ly


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
    src, dst, name = sys.argv[1:4]
    ly = read(src)
    (top,) = ly.top_cells()
    old = top.name
    top.name = name
    # area label of the seal ring PCell: area in mm2 instead of m2
    n_label = 0
    for c in ly.each_cell():
        if c.name != "sealring":
            continue
        for li in ly.layer_indexes():
            i = ly.get_info(li)
            if (i.layer, i.datatype) != (63, 0):
                continue
            for s in c.shapes(li).each():
                if s.is_text() and "Calculated area" in s.text_string:
                    m = re.search(r"x=([0-9.]+) um ; y=([0-9.]+) um", s.text_string)
                    area = float(m.group(1)) * float(m.group(2)) / 1e6
                    new = re.sub(r"Calculated area: \S+ sq mm", "Calculated area: %s sq mm" % round(area, 6), s.text_string)
                    print("label old:", repr(s.text_string))
                    print("label new:", repr(new))
                    s.text_string = new
                    n_label += 1
    assert n_label == 1, n_label
    opt = db.SaveLayoutOptions()
    opt.format = "GDS2"
    opt.write_context_info = False
    opt.gds2_no_zero_length_paths = True
    opt.gds2_max_vertex_count = 8000
    opt.gds2_max_cellname_length = 32000
    opt.gds2_libname = "LIB"
    opt.gds2_write_timestamps = True
    opt.dbu = 0.001
    ly.write(dst, opt)

    # proof against the input GDS
    a, b = read(src), read(dst)
    (ta,), (tb,) = a.top_cells(), b.top_cells()
    assert tb.name == name and len(b.top_cells()) == 1
    assert ta.bbox() == tb.bbox(), (ta.bbox(), tb.bbox())
    layers_a = {(a.get_info(li).layer, a.get_info(li).datatype): li for li in a.layer_indexes()}
    layers_b = {(b.get_info(li).layer, b.get_info(li).datatype): li for li in b.layer_indexes()}
    assert set(layers_a) == set(layers_b)
    for ld in sorted(layers_a):
        ra = db.Region(ta.begin_shapes_rec(layers_a[ld]))
        rb = db.Region(tb.begin_shapes_rec(layers_b[ld]))
        x = ra ^ rb
        assert x.is_empty(), (ld, x.count())
    xa = [t for t in texts(a, ta) if "Calculated area" not in t[2]]
    xb = [t for t in texts(b, tb) if "Calculated area" not in t[2]]
    assert xa == xb
    ca = sorted(c.name for c in a.each_cell() if c.cell_index() != ta.cell_index())
    cb = sorted(c.name for c in b.each_cell() if c.cell_index() != tb.cell_index())
    assert ca == cb
    print("top cell %s -> %s, %d layers equal by XOR, %d labels equal (without area label), subcells equal"
          % (old, name, len(layers_a), len(xa)))
    data = open(dst, "rb").read()
    print("%s  sha256 %s  %d bytes" % (dst, hashlib.sha256(data).hexdigest(), len(data)))


if __name__ == "__main__":
    main()
