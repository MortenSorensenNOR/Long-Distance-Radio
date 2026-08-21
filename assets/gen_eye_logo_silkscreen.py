import math

W, H = 1742, 903
cx, cy = 871.0, 346.0
half_chord = 456.5
R = 548.0
sagitta = R - math.sqrt(R*R - half_chord*half_chord)

left_tip = (cx - half_chord, cy)
right_tip = (cx + half_chord, cy)

cyA = cy + (R - sagitta)
cyB = cy - (R - sagitta)

iris_r = 231.0
pupil_r = 130.5

outline_w = 8.0
hatch_pitch = 12.0
hatch_stroke = 7.0

top_hw = 146.0
bot_hw = 236.0
y_top = cyB + math.sqrt(R*R - top_hw*top_hw)
y_bot = H

# Silkscreen-ready version: identical artwork to the main design (solid white
# sclera, hatched iris, hatched tail, black outline/pupil) but with a
# transparent canvas instead of a solid black background, so only the actual
# shapes carry pixels when this is fed into KiCad's Image Converter.
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <pattern id="hatch" patternUnits="userSpaceOnUse" width="{hatch_pitch}" height="{hatch_pitch}"
             patternTransform="translate({cx},{cy}) rotate(45) translate({-hatch_stroke/2},0)">
      <rect width="{hatch_pitch}" height="{hatch_pitch}" fill="#ffffff"/>
      <rect x="0" y="0" width="{hatch_stroke}" height="{hatch_pitch}" fill="#000000"/>
    </pattern>
    <mask id="tailMask">
      <rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>
      <path d="M {left_tip[0]},{left_tip[1]}
               A {R},{R} 0 0 1 {right_tip[0]},{right_tip[1]}
               A {R},{R} 0 0 1 {left_tip[0]},{left_tip[1]} Z"
            fill="#000000"/>
    </mask>
  </defs>

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

out = '/tmp/claude-1000/-home-morten-dev-Long-Distance-Radio/ad5b57b1-03d3-41e4-9778-6c246ea0e6be/scratchpad/eye_logo_silkscreen.svg'
with open(out, 'w') as f:
    f.write(svg)
print('wrote', out)
