#!/usr/bin/env python3
"""Perimeter via fence + exposed-copper mask band for CLK_BOARD.

Re-runnable: everything it creates is tagged into groups VIA_FENCE / VIA_FENCE_MASK
and wiped at the start of each run, so tweaking a parameter and re-running is safe.
"""
import math, sys
import pcbnew

MM = 1000000

# ---- tunables -------------------------------------------------------------
VIA_INSET   = 0.85   # board edge -> via centre (centres it in the 0.30-1.40 band)
VIA_DIA     = 0.45
VIA_DRILL   = 0.30
PITCH       = 2.00   # target arc-length pitch; actual is rounded to fit exactly
END_MARGIN  = 1.00   # wrap segments: gap from segment end to first/last via
END_MIN     = 0.30   # slivers: minimum clear gap at each end

BAND_IN     = 0.00   # board edge -> outer edge of band; the GND-copper
                     # intersection below clips it back to the pour edge
BAND_OUT    = 1.40   # board edge -> inner edge of exposed band
FILLET_R    = 0.50   # concave fillet where band meets mounting-hole discs

MASK_DAM    = 0.20   # mask kept around non-GND copper inside the band
VIA_CLR     = 0.20   # fence via copper -> other-net copper
PAD_MARGIN  = 0.15   # fence via copper -> same-net pad copper
VIAVIA_CLR  = 0.30   # fence via copper -> existing via copper

SMA_REFS    = ("J2", "J3", "J4", "J6", "J7", "J8")
SMA_CLEAR   = 0.30   # band stops this far outside each SMA pad group
SLIVER_A    = 0.05   # drop band fragments smaller than this (mm^2)
NUDGE_SILK  = True   # shift SMA refdes clear of the band (set False to leave silk alone)
SILK_CLR    = 0.15   # board min_silk_clearance

MTG_REFS    = ("H1", "H2", "H3", "H4")
MTG_DISC_R  = 2.20   # radius of the existing 4.4mm mounting pad

ARC_ERR     = 1000   # 0.001mm polygonisation error
# ---------------------------------------------------------------------------

BOARD = sys.argv[1] if len(sys.argv) > 1 else "CLK_BOARD.kicad_pcb"

TAGS = ("VIA_FENCE", "VIA_FENCE_MASK")


def strip_previous(path):
    """Delete everything a previous run added. Runs as its own process."""
    b = pcbnew.LoadBoard(path)
    doomed = []
    for seq in (b.GetTracks(), b.GetDrawings()):
        for item in seq:
            g = item.GetParentGroup()
            if g is not None and g.GetName() in TAGS:
                doomed.append(item)
    for item in doomed:
        b.Remove(item)
    for g in list(b.Groups()):
        if g.GetName() in TAGS:
            b.Remove(g)
    if doomed:
        b.Save(path)
    return len(doomed)


if "--clean-only" in sys.argv:
    # Calling BOARD.Remove() permanently breaks SWIG's ability to cast C++
    # return values for the rest of the process - even a fresh LoadBoard()
    # comes back as a raw SwigPyObject. So the wipe is done in a throwaway
    # process and the real work below always starts from an untouched load.
    print(f"removed {strip_previous(BOARD)} items from previous run")
    sys.exit(0)

import subprocess
subprocess.run([sys.executable, __file__, BOARD, "--clean-only"], check=True)

board = pcbnew.LoadBoard(BOARD)

F_Cu, B_Cu = pcbnew.F_Cu, pcbnew.B_Cu
F_Mask, B_Mask = pcbnew.F_Mask, pcbnew.B_Mask
gnd = board.GetNetsByName()["GND"]
GNDCODE = gnd.GetNetCode()

ROUND = pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS


def nm(x):
    return int(round(x * MM))


def poly_from_outline():
    ps = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(ps, True)
    return ps


def inflated(ps, amount_mm):
    out = pcbnew.SHAPE_POLY_SET(ps)
    out.Inflate(nm(amount_mm), ROUND, ARC_ERR)
    out.Simplify()
    return out


def sma_channel(fp):
    """The launch channel of one SMA: the span between its two ground pads.

    The band covers the ground pads and stops at their inner edges rather than
    carrying on across the coplanar gaps and the signal pad in between.
    """
    gnds, sig = [], []
    for pad in fp.Pads():
        (gnds if pad.GetNetCode() == GNDCODE else sig).append(pad)
    if not gnds or not sig:
        return None

    sb = sig[0].GetBoundingBox()
    sx = (int(sb.GetLeft()) + int(sb.GetRight())) // 2

    lefts = [int(p.GetBoundingBox().GetRight()) for p in gnds
             if int(p.GetBoundingBox().GetRight()) <= sx]
    rights = [int(p.GetBoundingBox().GetLeft()) for p in gnds
              if int(p.GetBoundingBox().GetLeft()) >= sx]
    if not lefts or not rights:
        return None

    ys = []
    for pad in fp.Pads():
        pb = pad.GetBoundingBox()
        ys += [int(pb.GetTop()), int(pb.GetBottom())]
    m = nm(1.0)  # overshoot so the cut clears the band in y
    x0, x1 = max(lefts), min(rights)
    y0, y1 = min(ys) - m, max(ys) + m

    r = pcbnew.SHAPE_POLY_SET()
    r.NewOutline()
    for (px, py) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        r.Append(px, py)
    return r


def sma_exclusion(board_):
    """Pad-group bbox of each SMA, grown by SMA_CLEAR.

    Both the fence and the band stop outside this. Keeping vias out matters as
    much as the mask: the gap between an SMA ground pad and its signal pad is
    wide enough to drop a via into without tripping any clearance rule, but it
    sits right in the launch.
    """
    ex = pcbnew.SHAPE_POLY_SET()
    for fp in board_.GetFootprints():
        if fp.GetReference() not in SMA_REFS:
            continue
        xs, ys = [], []
        for pad in fp.Pads():
            pb = pad.GetBoundingBox()
            xs += [int(pb.GetLeft()), int(pb.GetRight())]
            ys += [int(pb.GetTop()), int(pb.GetBottom())]
        if not xs:
            continue
        m = nm(SMA_CLEAR)
        x0, x1 = min(xs) - m, max(xs) + m
        y0, y1 = min(ys) - m, max(ys) + m
        r = pcbnew.SHAPE_POLY_SET()
        r.NewOutline()
        for (px, py) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            r.Append(px, py)
        ex.BooleanAdd(r)
    ex.Simplify()
    return ex


# ---- 1. even-arc-length via lattice --------------------------------------
outline = poly_from_outline()
via_path_ps = inflated(outline, -VIA_INSET)
# Read vertices straight off the poly set. Going via Outline(0) hands back a
# SHAPE_LINE_CHAIN that SWIG sometimes fails to cast on a mutated board.
pts = [(via_path_ps.CVertex(i, 0, -1).x, via_path_ps.CVertex(i, 0, -1).y)
       for i in range(via_path_ps.VertexCount(0, -1))]
segs, total = [], 0.0
for i in range(len(pts)):
    a, b = pts[i], pts[(i + 1) % len(pts)]
    d = math.hypot(b[0] - a[0], b[1] - a[1])
    if d > 0:
        segs.append((total, d, a, b))
        total += d

print(f"via path perimeter {total/MM:.3f} mm")


def point_at(s):
    s %= total
    lo, hi = 0, len(segs) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if segs[mid][0] <= s:
            lo = mid
        else:
            hi = mid - 1
    s0, d, a, b = segs[lo]
    t = (s - s0) / d
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


# ---- 2. keepout for the vias ---------------------------------------------
keepout = pcbnew.SHAPE_POLY_SET()
vr = VIA_DIA / 2.0


def add_shape(item, clearance, layer=None):
    tmp = pcbnew.SHAPE_POLY_SET()
    try:
        item.TransformShapeToPolySet(tmp, layer if layer is not None else item.GetLayer(),
                                     nm(clearance), ARC_ERR, pcbnew.ERROR_OUTSIDE)
    except Exception:
        return
    keepout.BooleanAdd(tmp)


for fp in board.GetFootprints():
    is_mtg = fp.GetReference() in MTG_REFS
    for pad in fp.Pads():
        same = pad.GetNetCode() == GNDCODE
        # The mounting-hole pads are bare GND copper discs with nothing soldered to
        # them, so the fence may run straight across; only drill spacing matters.
        if not is_mtg:
            clr = (PAD_MARGIN if same else VIA_CLR) + vr
            for ly in (F_Cu, B_Cu):
                if pad.IsOnLayer(ly):
                    add_shape(pad, clr, ly)
        if pad.GetDrillSizeX() > 0:  # keep drills apart
            c = pad.GetPosition()
            circ = pcbnew.SHAPE_POLY_SET()
            circ.NewOutline()
            r = pad.GetDrillSizeX() / 2 + nm(0.254) + nm(VIA_DRILL / 2)
            for k in range(48):
                ang = 2 * math.pi * k / 48
                circ.Append(int(c.x + r * math.cos(ang)), int(c.y + r * math.sin(ang)))
            keepout.BooleanAdd(circ)

for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        c = t.GetPosition()
        r = t.GetWidth() / 2 + nm(VIAVIA_CLR) + nm(vr)
        circ = pcbnew.SHAPE_POLY_SET()
        circ.NewOutline()
        for k in range(48):
            ang = 2 * math.pi * k / 48
            circ.Append(int(c.x + r * math.cos(ang)), int(c.y + r * math.sin(ang)))
        keepout.BooleanAdd(circ)
    elif t.GetNetCode() != GNDCODE:
        add_shape(t, VIA_CLR + vr)

for z in board.Zones():
    if z.GetNetCode() != GNDCODE and not z.GetIsRuleArea():
        for ly in (F_Cu, B_Cu):
            if z.IsOnLayer(ly):
                fp_ = z.GetFilledPolysList(ly)
                if fp_:
                    tmp = pcbnew.SHAPE_POLY_SET(fp_)
                    tmp.Inflate(nm(VIA_CLR + vr), ROUND, ARC_ERR)
                    keepout.BooleanAdd(tmp)

SMA_EX = sma_exclusion(board)
keepout.BooleanAdd(SMA_EX)
keepout.Simplify()


# ---- 3. one independent, self-centred run of vias per band segment --------
# The band is cut into disconnected pieces by the SMA exclusions. Rather than
# laying one lattice around the whole loop and deleting whatever collides -
# which leaves each piece with an arbitrary phase - each piece gets its own
# evenly spaced run, placed symmetrically inside that piece.

def blocked(s):
    p = point_at(s)
    return keepout.Contains(pcbnew.VECTOR2I(int(p[0]), int(p[1])))


SAMPLE = nm(0.02)
nsamp = int(total // SAMPLE)
free = [not blocked(i * SAMPLE) for i in range(nsamp)]

def refine(s_blocked, s_free):
    """Bisect onto the exact blocked/free transition; returns the free side.

    Without this the segment ends land on the 0.02mm sample grid, which is
    enough to make nominally symmetric segments disagree by ~0.02mm.
    """
    lo, hi = float(s_blocked), float(s_free)
    for _ in range(40):
        mid = (lo + hi) / 2.0
        if blocked(mid):
            lo = mid
        else:
            hi = mid
    return hi


if all(free):
    runs = [(0.0, total)]
else:
    runs = []
    for i in range(nsamp):
        if free[i] and not free[(i - 1) % nsamp]:
            e = i
            while free[(e + 1) % nsamp] and (e - i) < nsamp:
                e += 1
            runs.append((refine((i - 1) * SAMPLE, i * SAMPLE),
                         refine((e + 1) * SAMPLE, e * SAMPLE)))

print(f"{len(runs)} band segment(s) on the via path")


def x_at(s):
    return point_at(s)[0]


def reach(s_from, direction, target, sign, limit):
    """March from s_from until x passes target, then interpolate onto it exactly."""
    step = nm(0.01) * direction
    s, travelled = s_from, 0.0
    prev, prev_x = s_from, x_at(s_from)
    while travelled < limit:
        s += step
        travelled += abs(step)
        cur_x = x_at(s)
        if sign * (cur_x - target) >= 0:
            if cur_x != prev_x:
                return prev + (s - prev) * (target - prev_x) / (cur_x - prev_x)
            return s
        prev, prev_x = s, cur_x
    return None


placed = []
report = []
for (s0, s1) in runs:
    L = s1 - s0
    p0, p1 = point_at(s0), point_at(s1)
    same_run = abs(p0[1] - p1[1]) < nm(0.01) and abs(p0[0] - p1[0]) < L + nm(0.01)

    if same_run:
        # A sliver between two SMAs: centre the vias on it, so one lands dead
        # centre, or two/three sit symmetrically about the centre.
        n = int((L - 2 * nm(END_MIN)) // nm(PITCH)) + 1
        n = max(0, n)
        mid = (s0 + s1) / 2.0
        arcs = [mid + (k - (n - 1) / 2.0) * nm(PITCH) for k in range(n)]
        kind = "sliver"
    else:
        # A long wrap-around segment: anchor the first and last via to the same
        # x so the two ends line up with each other down the board.
        x0, x1 = p0[0], p1[0]
        sign = 1 if x_at(s0 + nm(0.2)) > x0 else -1
        target = (max(x0, x1) if sign > 0 else min(x0, x1)) + sign * nm(END_MARGIN)
        a = reach(s0, +1, target, sign, L / 2)
        b = reach(s1, -1, target, sign, L / 2)
        if a is None or b is None:
            a, b = s0 + nm(END_MARGIN), s1 - nm(END_MARGIN)
        span = b - a
        n = max(2, int(round(span / nm(PITCH))) + 1)
        arcs = [a + span * k / (n - 1) for k in range(n)]
        kind = "wrap"

    kept = []
    for s in arcs:
        p = point_at(s)
        if keepout.Contains(pcbnew.VECTOR2I(int(p[0]), int(p[1]))):
            continue
        kept.append((int(p[0]), int(p[1])))
    placed += kept
    pitch = (arcs[1] - arcs[0]) / MM if len(arcs) > 1 else 0.0
    report.append((kind, L / MM, len(arcs), len(arcs) - len(kept), pitch,
                   point_at(arcs[0]) if arcs else None,
                   point_at(arcs[-1]) if arcs else None))

for kind, L, n, dropped, pitch, first, last in report:
    ends = ""
    if first and last:
        ends = "  first x=%.3f last x=%.3f" % (first[0] / MM, last[0] / MM)
    print("  %-6s len %6.2f mm -> %2d via(s), pitch %.3f mm%s%s"
          % (kind, L, n, pitch, ends, "  (%d dropped)" % dropped if dropped else ""))

print(f"{len(placed)} fence vias placed")


# ---- 4. create the vias ---------------------------------------------------
grp = pcbnew.PCB_GROUP(board)
grp.SetName("VIA_FENCE")
board.Add(grp)

for (x, y) in placed:
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(x, y))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(F_Cu, B_Cu)
    v.SetWidth(nm(VIA_DIA))
    v.SetDrill(nm(VIA_DRILL))
    v.SetNetCode(GNDCODE)
    v.SetFrontTentingMode(pcbnew.TENTING_MODE_NOT_TENTED)
    v.SetBackTentingMode(pcbnew.TENTING_MODE_NOT_TENTED)
    board.Add(v)
    grp.AddItem(v)


# ---- 5. mask band ---------------------------------------------------------
band = inflated(outline, -BAND_IN)
hole = inflated(outline, -BAND_OUT)
band.BooleanSubtract(hole)

# merge the mounting-hole discs in
for fp in board.GetFootprints():
    if fp.GetReference() in MTG_REFS:
        c = fp.GetPosition()
        disc = pcbnew.SHAPE_POLY_SET()
        disc.NewOutline()
        r = nm(MTG_DISC_R)
        for k in range(128):
            ang = 2 * math.pi * k / 128
            disc.Append(int(c.x + r * math.cos(ang)), int(c.y + r * math.sin(ang)))
        band.BooleanAdd(disc)
band.Simplify()

# morphological close -> rounds the concave junctions into fillets
band.Inflate(nm(FILLET_R), ROUND, ARC_ERR)
band.Inflate(-nm(FILLET_R), ROUND, ARC_ERR)
band.Simplify()

mgrp = pcbnew.PCB_GROUP(board)
mgrp.SetName("VIA_FENCE_MASK")
board.Add(mgrp)

for cu, mask in ((F_Cu, F_Mask), (B_Cu, B_Mask)):
    layer_band = pcbnew.SHAPE_POLY_SET(band)

    # keep solder mask around anything that is not GND, so the band never
    # bridges a signal pad to the surrounding pour
    cut = pcbnew.SHAPE_POLY_SET()
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetCode() != GNDCODE and pad.IsOnLayer(cu):
                tmp = pcbnew.SHAPE_POLY_SET()
                pad.TransformShapeToPolySet(tmp, cu, nm(MASK_DAM), ARC_ERR, pcbnew.ERROR_OUTSIDE)
                cut.BooleanAdd(tmp)
    for t in board.GetTracks():
        if t.GetNetCode() != GNDCODE and t.IsOnLayer(cu) and not isinstance(t, pcbnew.PCB_VIA):
            tmp = pcbnew.SHAPE_POLY_SET()
            t.TransformShapeToPolySet(tmp, cu, nm(MASK_DAM), ARC_ERR, pcbnew.ERROR_OUTSIDE)
            cut.BooleanAdd(tmp)
    for z in board.Zones():
        if z.GetNetCode() != GNDCODE and not z.GetIsRuleArea() and z.IsOnLayer(cu):
            fp_ = z.GetFilledPolysList(cu)
            if fp_:
                tmp = pcbnew.SHAPE_POLY_SET(fp_)
                tmp.Inflate(nm(MASK_DAM), ROUND, ARC_ERR)
                cut.BooleanAdd(tmp)
    # Cover each SMA's ground pads, then stop. Only cut the channel on layers
    # that actually carry the signal pad - the back has no launch to protect,
    # so it stays one continuous ring.
    for fp in board.GetFootprints():
        if fp.GetReference() not in SMA_REFS:
            continue
        if not any(p.GetNetCode() != GNDCODE and p.IsOnLayer(cu) for p in fp.Pads()):
            continue
        ch = sma_channel(fp)
        if ch is not None:
            cut.BooleanAdd(ch)

    cut.Simplify()
    layer_band.BooleanSubtract(cut)

    # Guarantee every exposed spot actually has GND copper under it, so the
    # opening can never reveal bare laminate.
    gndcu = pcbnew.SHAPE_POLY_SET()
    for z in board.Zones():
        if z.GetNetCode() == GNDCODE and not z.GetIsRuleArea() and z.IsOnLayer(cu):
            fz = z.GetFilledPolysList(cu)
            if fz:
                gndcu.BooleanAdd(pcbnew.SHAPE_POLY_SET(fz))
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetCode() == GNDCODE and pad.IsOnLayer(cu):
                tmp = pcbnew.SHAPE_POLY_SET()
                pad.TransformShapeToPolySet(tmp, cu, 0, ARC_ERR, pcbnew.ERROR_INSIDE)
                gndcu.BooleanAdd(tmp)
    gndcu.Simplify()
    layer_band.BooleanIntersection(gndcu)
    layer_band.Simplify()

    # drop stray fragments left behind by the clipping
    keep = pcbnew.SHAPE_POLY_SET()
    dropped = 0
    for i in range(layer_band.OutlineCount()):
        one = pcbnew.SHAPE_POLY_SET()
        one.NewOutline()
        for k in range(layer_band.VertexCount(i, -1)):
            v = layer_band.CVertex(k, i, -1)
            one.Append(v.x, v.y)
        # The holes have to come along: when the band is uninterrupted it is a
        # single ring whose hole is the whole board interior, and rebuilding it
        # from the outer boundary alone would flood the board with mask opening.
        for h in range(layer_band.HoleCount(i)):
            one.NewHole()
            for k in range(layer_band.VertexCount(i, h)):
                v = layer_band.CVertex(k, i, h)
                one.Append(v.x, v.y, 0, one.HoleCount(0) - 1)
        if one.Area() < SLIVER_A * MM * MM:
            dropped += 1
            continue
        keep.BooleanAdd(one)
    keep.Simplify()
    layer_band = keep
    if dropped:
        print(f"  dropped {dropped} sliver fragment(s) on {pcbnew.LayerName(mask)}")

    for i in range(layer_band.OutlineCount()):
        sub = pcbnew.SHAPE_POLY_SET()
        sub.NewOutline()
        for k in range(layer_band.VertexCount(i, -1)):
            v = layer_band.CVertex(k, i, -1)
            sub.Append(v.x, v.y)
        for h in range(layer_band.HoleCount(i)):
            sub.NewHole()
            for k in range(layer_band.VertexCount(i, h)):
                v = layer_band.CVertex(k, i, h)
                sub.Append(v.x, v.y, i, sub.HoleCount(i) - 1)
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_POLY)
        s.SetPolyShape(sub)
        s.SetLayer(mask)
        s.SetFilled(True)
        s.SetWidth(0)
        board.Add(s)
        mgrp.AddItem(s)
    print(f"{pcbnew.LayerName(mask)}: {layer_band.OutlineCount()} band polygon(s)")


# ---- 6. keep the SMA refdes out of the new mask opening --------------------
# The band exposes copper under the J2..J8 labels, and KiCad clips silkscreen
# wherever it crosses a mask opening. Nudge each label inward just far enough
# to clear. The original position is stashed so re-runs stay idempotent.
if NUDGE_SILK:
    fband = pcbnew.SHAPE_POLY_SET()
    for d in board.GetDrawings():
        if d.GetLayer() == F_Mask and d.GetShape() == pcbnew.SHAPE_T_POLY:
            fband.BooleanAdd(d.GetPolyShape())
    guard = pcbnew.SHAPE_POLY_SET(fband)
    guard.Inflate(nm(SILK_CLR), ROUND, ARC_ERR)
    guard.Simplify()

    cx = (outline.BBox().GetLeft() + outline.BBox().GetRight()) / 2.0
    cy = (outline.BBox().GetTop() + outline.BBox().GetBottom()) / 2.0

    def clashes(txt):
        bb = txt.GetBoundingBox()
        x0, x1 = int(bb.GetLeft()), int(bb.GetRight())
        y0, y1 = int(bb.GetTop()), int(bb.GetBottom())
        r = pcbnew.SHAPE_POLY_SET()
        r.NewOutline()
        for (px, py) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            r.Append(px, py)
        t = pcbnew.SHAPE_POLY_SET(r)
        t.BooleanIntersection(guard)
        return t.Area() > 0

    moved = []
    for fp in board.GetFootprints():
        if fp.GetReference() not in SMA_REFS:
            continue
        txt = fp.Reference()
        if not txt.IsVisible():
            continue

        # Restore any previous nudge first, so re-runs are idempotent. Stored
        # relative to the footprint origin so it survives the part being moved.
        key = "VIAFENCE_SILK_ORIG"
        fpos = fp.GetPosition()
        if fp.HasField(key):
            ox, oy = (int(v) for v in fp.GetFieldText(key).split(","))
            txt.SetPosition(pcbnew.VECTOR2I(fpos.x + ox, fpos.y + oy))
        else:
            fp.SetField(key, "%d,%d" % (txt.GetPosition().x - fpos.x,
                                        txt.GetPosition().y - fpos.y))
            fp.GetField(key).SetVisible(False)

        start = txt.GetPosition()
        # inward = toward board centre, along whichever axis the label is nearest an edge
        dx = 0 if abs(start.x - cx) < abs(start.y - cy) else (1 if start.x < cx else -1)
        dy = 0 if dx else (1 if start.y < cy else -1)

        step = nm(0.05)
        shifted = 0
        while clashes(txt) and shifted < nm(2.0):
            shifted += step
            txt.SetPosition(pcbnew.VECTOR2I(start.x + dx * shifted, start.y + dy * shifted))
        if shifted:
            moved.append((fp.GetReference(), shifted / MM))

    if moved:
        print("nudged refdes clear of band: " +
              ", ".join(f"{r} by {d:.2f}mm" for r, d in moved))
    else:
        print("no refdes needed nudging")

board.Save(BOARD)
print("saved", BOARD)
