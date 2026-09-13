#!/usr/bin/env python3
"""Centre the two SMA rows on the board's x centreline.

Both rows keep their 10mm pitch; the middle connector of each row lands on the
board centre, so the rows line up with each other and the whole edge becomes
left/right symmetric. Run viafence.py afterwards to regenerate the fence.
"""
import sys
import pcbnew

MM = 1000000
BOARD = sys.argv[1] if len(sys.argv) > 1 else "CLK_BOARD.kicad_pcb"
SILK_KEY = "VIAFENCE_SILK_ORIG"
ROWS = {"J2": -1, "J3": 0, "J4": +1, "J6": -1, "J7": 0, "J8": +1}
SPACING = 10.0

board = pcbnew.LoadBoard(BOARD)

bb = pcbnew.SHAPE_POLY_SET()
board.GetBoardPolygonOutlines(bb, True)
box = bb.BBox()
centre_x = (int(box.GetLeft()) + int(box.GetRight())) // 2
print("board centre x = %.4f mm" % (centre_x / MM))

for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
    ref = fp.GetReference()
    if ref not in ROWS:
        continue

    old = fp.GetPosition()
    new_x = centre_x + int(round(ROWS[ref] * SPACING * MM))
    dx = new_x - old.x
    if dx == 0:
        print("  %-3s already at %.4f" % (ref, old.x / MM))
        continue

    # The silk stash is absolute and pre-nudge; convert it to an offset from the
    # footprint origin, which is invariant under the move. viafence.py reads it
    # back in that form.
    rel = None
    if fp.HasField(SILK_KEY):
        ox, oy = (int(v) for v in fp.GetFieldText(SILK_KEY).split(","))
        rel = (ox - old.x, oy - old.y)

    fp.SetPosition(pcbnew.VECTOR2I(new_x, old.y))

    if rel is not None:
        fp.SetField(SILK_KEY, "%d,%d" % rel)
        fp.GetField(SILK_KEY).SetVisible(False)

    print("  %-3s x %.4f -> %.4f  (dx %+.4f mm)" % (ref, old.x / MM, new_x / MM, dx / MM))

# Moving the parts invalidates the pours - the old fills still carry the
# cut-outs for the previous pad positions, which leaves the launch pads sitting
# in stale GND copper. Refill before anything else reads the zone geometry.
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
print("refilled %d zone(s)" % len(list(board.Zones())))

board.Save(BOARD)
print("saved", BOARD)
