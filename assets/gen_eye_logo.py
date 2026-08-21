import math

W, H = 1742, 903
cx, cy = 871.0, 346.0
half_chord = 456.5
R = 548.0
sagitta = R - math.sqrt(R*R - half_chord*half_chord)

left_tip = (cx - half_chord, cy)
right_tip = (cx + half_chord, cy)

# circle A (below chord) -> upper arc bulges up
cyA = cy + (R - sagitta)
# circle B (above chord) -> lower arc bulges down
cyB = cy - (R - sagitta)

top_apex_y = cyA - R
bot_apex_y = cyB + R

iris_r = 231.0
pupil_r = 130.5

outline_w = 8.0
hatch_pitch = 12.0
hatch_stroke = 7.0

# tail geometry: a trapezoid whose flat top is wider than the eye curve at the
# same height, so the tail visibly flares out past the lower lid as it narrows
# to its point (this is what makes it "hug" the eye instead of pinching off
# into a separate spike). The overlap between the trapezoid and the eye's own
# interior is subtracted out with a mask below, so hatching only ever appears
# outside the white sclera, never on top of it.
top_hw = 146.0
bot_hw = 236.0
y_top = cyB + math.sqrt(R*R - top_hw*top_hw)
y_bot = H  # run to canvas edge

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <!-- phase-locked to the iris center: the local origin (pre-translate) sits at
         a stripe *center* (stroke/2), and the whole grid is then recentered on
         (cx,cy), giving the hatch exact 180-degree point symmetry about the iris
         center. That makes the partial slivers at opposite edges of the iris
         circle always come out equal, instead of one nearly-full stripe on one
         side and a razor sliver on the other. -->
    <pattern id="hatch" patternUnits="userSpaceOnUse" width="{hatch_pitch}" height="{hatch_pitch}"
             patternTransform="translate({cx},{cy}) rotate(45) translate({-hatch_stroke/2},0)">
      <rect width="{hatch_pitch}" height="{hatch_pitch}" fill="#ffffff"/>
      <rect x="0" y="0" width="{hatch_stroke}" height="{hatch_pitch}" fill="#000000"/>
    </pattern>
    <clipPath id="eyeClip">
      <path d="M {left_tip[0]},{left_tip[1]}
               A {R},{R} 0 0 1 {right_tip[0]},{right_tip[1]}
               A {R},{R} 0 0 1 {left_tip[0]},{left_tip[1]} Z"/>
    </clipPath>
    <!-- white = visible, black = hidden: knocks the eye's own interior out of
         whatever this mask is applied to, so the tail can flare past the lid
         curve without ever painting over the white sclera -->
    <mask id="tailMask">
      <rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>
      <path d="M {left_tip[0]},{left_tip[1]}
               A {R},{R} 0 0 1 {right_tip[0]},{right_tip[1]}
               A {R},{R} 0 0 1 {left_tip[0]},{left_tip[1]} Z"
            fill="#000000"/>
    </mask>
  </defs>

  <rect x="0" y="0" width="{W}" height="{H}" fill="#000000"/>

  <!-- eye white fill -->
  <path d="M {left_tip[0]},{left_tip[1]}
           A {R},{R} 0 0 1 {right_tip[0]},{right_tip[1]}
           A {R},{R} 0 0 1 {left_tip[0]},{left_tip[1]} Z"
        fill="#ffffff"/>

  <!-- tail (beam) trapezoid, hatched, masked so it can only paint outside the
       eye's own interior -->
  <path d="M {cx-top_hw},{y_top}
           L {cx+top_hw},{y_top}
           L {cx+bot_hw},{y_bot}
           L {cx-bot_hw},{y_bot} Z"
        fill="url(#hatch)" mask="url(#tailMask)"/>

  <!-- eye outline stroke, drawn on top so it stays crisp over the tail -->
  <path d="M {left_tip[0]},{left_tip[1]}
           A {R},{R} 0 0 1 {right_tip[0]},{right_tip[1]}
           A {R},{R} 0 0 1 {left_tip[0]},{left_tip[1]} Z"
        fill="none" stroke="#000000" stroke-width="{outline_w}"/>

  <!-- iris outer ring, hatched, with outline -->
  <path d="M {cx-iris_r},{cy}
           a {iris_r},{iris_r} 0 1 0 {2*iris_r},0
           a {iris_r},{iris_r} 0 1 0 {-2*iris_r},0 Z
           M {cx-pupil_r},{cy}
           a {pupil_r},{pupil_r} 0 1 0 {2*pupil_r},0
           a {pupil_r},{pupil_r} 0 1 0 {-2*pupil_r},0 Z"
        fill="url(#hatch)" fill-rule="evenodd"
        stroke="#000000" stroke-width="{outline_w}"/>

  <!-- pupil solid black -->
  <circle cx="{cx}" cy="{cy}" r="{pupil_r}" fill="#000000"/>
</svg>
'''

with open('/tmp/claude-1000/-home-morten-dev-Long-Distance-Radio/ad5b57b1-03d3-41e4-9778-6c246ea0e6be/scratchpad/eye_clean.svg', 'w') as f:
    f.write(svg)

print('sagitta', sagitta, 'top_apex_y', top_apex_y, 'bot_apex_y', bot_apex_y, 'y_top', y_top)
