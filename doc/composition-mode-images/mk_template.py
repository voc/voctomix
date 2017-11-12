#!/usr/bin/env python3

width = 1920
height = 1080

side_by_side_equal = {
    "gutter": 20,
    "atop": 160,
    "btop": 480
}

side_by_side_preview = {
    "aleft": 20,
    "atop": 160,
    "awidth": 1420,
    "aheight": 799,
    "bleft": 1404,
    "btop": 781,
    "bwidth": 496,
    "bheight": 279
}

rump = 4./9. * height
head_x = 2./9. * height
neck_sleeve = 1./6. * height
shoulder = 11./36. * height
shoulder_curve = 5./18. * height

path = """
m {start_x:.2f} {start_y:.2f}
v -{inner_arm:.2f} {inner_arm:.2f}
h {rump:.2f}
v -{inner_arm:.2f} {inner_arm:.2f}
h {neck_sleeve:.2f}
c 0 -{inner_arm:.2f}
  -{shoulder_div:.2f} -{outter_arm:.2f}
  -{shoulder:.2f} -{outter_arm:.2f}
  {head_xl:.2f} -{head_y:.2f}
  -{head_xr:.2f} -{head_y:.2f}
  -{neck_sleeve:.2f} 0
  -{shoulder_curve:.2f} 0
  -{shoulder:.2f} {neck_sleeve:.2f}
  -{shoulder:.2f} {outter_arm:.2f}
z
""".format(
    inner_arm=1./3. * height,
    outter_arm=1./2. * height,
    neck_sleeve=neck_sleeve,
    rump=rump,
    start_x=(width - rump) / 2.,
    start_y=height - 15.,
    head_xl=head_x,
    head_xr=head_x + neck_sleeve,
    head_y=5./12. * height,
    shoulder=shoulder,
    shoulder_curve=shoulder_curve,
    shoulder_div=shoulder - shoulder_curve
)

gutter = side_by_side_equal["gutter"]

svg = r"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}"
    height="{height}"
    version="1.1"
    viewBox="0 0 {width} {height}"
    xmlns="http://www.w3.org/2000/svg"
    xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
    xmlns:xlink="http://www.w3.org/1999/xlink">
  <g id="background" inkscape:groupmode="layer">
    <rect width="{width}" height="{height}" style="fill:#fff"/>
  </g>
  <g id="full_camera" inkscape:groupmode="layer" style="display:none">
    <g id="camera" style="display:inline">
      <rect width="{width}" height="{height}" style="fill:#0f0"/>
      <path d="{path}"
          style="display:inline;fill-rule:evenodd;fill:#001eff;
                 stroke-linejoin:round;stroke-width:30;stroke:#004fff"/>
    </g>
  </g>
  <g id="full_slide" inkscape:groupmode="layer" style="display:none">
    <g id="slide" style="display:inline">
      <rect width="{width}" height="{height}" style="fill:#000080"/>
      <rect x="{tleft}" y="{ttop}"
          width="{twidth:.2f}" height="{theight:.2f}"
          ry="{tround:.2f}" style="fill:#8080ff"/>
    </g>
  </g>
  <g id="side_by_side_preview" inkscape:groupmode="layer" style="display:none">
    <use transform="matrix({sspa_xscale:.6f} 0 0 {sspa_yscale:.6f}
                           {sspax} {sspay})"
        width="100%" height="100%"
        xlink:href="#slide"/>
    <use transform="matrix({sspb_xscale:.6f} 0 0 {sspb_yscale:.6f}
                           {sspbx} {sspby})"
        width="100%" height="100%"
        xlink:href="#camera"/>
  </g>
  <g id="side_by_side_equal" inkscape:groupmode="layer">
    <use transform="matrix({sse_scale:.6f} 0 0 {sse_scale:.6f} 0 {ssea})"
        width="100%" height="100%"
        xlink:href="#slide"/>
    <use transform="matrix({sse_scale:.6f} 0 0 {sse_scale:.6f}
                           {ssebx} {sseby})"
        width="100%" height="100%"
        xlink:href="#camera"/>
  </g>
</svg>
""".format(
    width=width,
    height=height,
    twidth=3./4. * width,
    theight=1./5. * height,
    tround=1./20. * height,
    ttop=1./5. * height,
    tleft=1./8. * width,
    sspa_xscale=side_by_side_preview["awidth"] / float(width),
    sspa_yscale=side_by_side_preview["aheight"] / float(height),
    sspax=side_by_side_preview["aleft"],
    sspay=side_by_side_preview["atop"],
    sspb_xscale=side_by_side_preview["bwidth"] / float(width),
    sspb_yscale=side_by_side_preview["bheight"] / float(height),
    sspbx=side_by_side_preview["bleft"],
    sspby=side_by_side_preview["btop"],
    sse_scale=(width - gutter) / (2. * width),
    ssea=side_by_side_equal["atop"],
    ssebx=(width - gutter) / 2. + gutter,
    sseby=side_by_side_equal["btop"],
    path=path
)

print(svg)
