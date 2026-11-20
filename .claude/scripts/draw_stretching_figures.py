#!/usr/bin/env python3
"""Draw the figures of teoria/10-esercizi-stretching.md in a flat-illustration style.

One SVG per exercise, two panels side by side:
- left: a male runner (t-shirt, shorts, running shoes) in the pose, with a support
  (wall, low wall, tree) where needed; the stretched muscle is tinted red;
- right: the same runner standing, in neutral colours, front or back view, with
  the stretched muscle in red and its name.

Bodies are built from tapered capsules (limbs), so a pose is just a set of joints.

Usage:
    python3 .claude/scripts/draw_stretching_figures.py
"""

import math
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "teoria" / "img" / "10-stretching"

W, H = 560, 310
GROUND_Y = 266
FONT = 'font-family="system-ui, -apple-system, Segoe UI, Roboto, sans-serif"'
BG, TEXT, MUTED = "#ffffff", "#2f2f2c", "#8a897f"
MUSCLE = "#e0453a"

ACTIVE = {"skin": "#f1c6a0", "skin_far": "#dcaa82", "shirt": "#2f78d0", "shirt_far": "#245fa8",
          "shorts": "#24272d", "shorts_far": "#15171b", "shoe": "#2f78d0", "shoe_far": "#245fa8",
          "sole": "#ffffff", "hair": "#3b2a1f"}
NEUTRAL = {"skin": "#e9e6e0", "skin_far": "#dedad2", "shirt": "#d3d0c8", "shirt_far": "#c7c3ba",
           "shorts": "#bdb9af", "shorts_far": "#b1ada3", "shoe": "#c7c3ba", "shoe_far": "#bdb9af",
           "sole": "#f4f2ee", "hair": "#b5b0a5"}
PROP, PROP_DARK, LEAF = "#d9c7a7", "#c4ae88", "#9fc58e"


# ---------- primitives ----------

def capsule(p, q, r1, r2, color, opacity=1.0):
    """Tapered limb from p (radius r1) to q (radius r2)."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    d = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / d, dx / d
    pts = [(p[0] + nx * r1, p[1] + ny * r1), (q[0] + nx * r2, q[1] + ny * r2),
           (q[0] - nx * r2, q[1] - ny * r2), (p[0] - nx * r1, p[1] - ny * r1)]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    op = f' opacity="{opacity}"' if opacity < 1 else ""
    return (f'<g{op}><polygon points="{poly}" fill="{color}"/>'
            f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="{r1}" fill="{color}"/>'
            f'<circle cx="{q[0]:.1f}" cy="{q[1]:.1f}" r="{r2}" fill="{color}"/></g>')


def lerp(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def circle(c, r, color):
    return f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{r}" fill="{color}"/>'


def text(x, y, s, size=13, anchor="start", weight="400", color=TEXT):
    return f'<text x="{x}" y="{y}" {FONT} font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{s}</text>'


# ---------- body parts ----------

def arm(sh, el, wr, pal, far=False):
    skin = pal["skin_far" if far else "skin"]
    shirt = pal["shirt_far" if far else "shirt"]
    out = capsule(sh, el, 7.5, 6, skin) + capsule(el, wr, 6, 4.8, skin)
    out += capsule(sh, lerp(sh, el, 0.42), 9, 8, shirt)          # sleeve
    hand = lerp(el, wr, 1.12)
    out += circle(hand, 5.6, skin)
    return out


def leg(hip, knee, ankle, toe, pal, far=False):
    skin = pal["skin_far" if far else "skin"]
    shorts = pal["shorts_far" if far else "shorts"]
    shoe = pal["shoe_far" if far else "shoe"]
    out = capsule(hip, knee, 12, 8.5, skin) + capsule(knee, ankle, 8.5, 5.5, skin)
    out += capsule(hip, lerp(hip, knee, 0.5), 13.5, 11.5, shorts)  # shorts leg
    out += capsule(ankle, toe, 6.5, 5, shoe)
    out += capsule(lerp(ankle, toe, 0.05), lerp(ankle, toe, 1.0), 3.2, 3, pal["sole"], 0.9).replace(
        "<g", f'<g transform="translate(0,4)"', 1)
    return out


def head_side(c, facing, pal):
    hx, hy = c
    hair = (f'<path d="M{hx - 15 * facing:.1f},{hy + 2} Q{hx - 16 * facing:.1f},{hy - 17} {hx + 2 * facing:.1f},{hy - 16} '
            f'Q{hx + 13 * facing:.1f},{hy - 15} {hx + 14 * facing:.1f},{hy - 6} L{hx - 2 * facing:.1f},{hy - 7} '
            f'Q{hx - 6 * facing:.1f},{hy + 1} {hx - 15 * facing:.1f},{hy + 2} Z" fill="{pal["hair"]}"/>')
    ear = circle((hx - 3 * facing, hy + 1), 3.2, pal["skin_far"])
    nose = circle((hx + 14 * facing, hy + 2), 3, pal["skin"])
    return circle(c, 15, pal["skin"]) + nose + hair + ear


def head_front(c, pal, back=False):
    hx, hy = c
    out = circle((hx - 15, hy + 2), 3.4, pal["skin_far"]) + circle((hx + 15, hy + 2), 3.4, pal["skin_far"])  # ears
    out += circle(c, 15, pal["skin"])
    if back:
        out += (f'<path d="M{hx - 15},{hy + 4} Q{hx - 16},{hy - 17} {hx},{hy - 17} Q{hx + 16},{hy - 17} {hx + 15},{hy + 4} '
                f'Q{hx},{hy + 10} {hx - 15},{hy + 4} Z" fill="{pal["hair"]}"/>')
    else:
        out += (f'<path d="M{hx - 15},{hy - 1} Q{hx - 15},{hy - 17} {hx},{hy - 17} Q{hx + 15},{hy - 17} {hx + 15},{hy - 1} '
                f'Q{hx + 6},{hy - 10} {hx - 15},{hy - 1} Z" fill="{pal["hair"]}"/>')
    return out


def torso_side(hip, sh, pal):
    neck = lerp(hip, sh, 1.13)
    return (capsule(sh, neck, 6, 5.5, pal["skin"]) + capsule(hip, sh, 15, 16, pal["shirt"])
            + circle(hip, 15.5, pal["shorts"]))


def torso_front(cx, sh_y, hip_y, pal):
    return (capsule((cx, sh_y - 8), (cx, sh_y - 16), 6, 6, pal["skin"])
            + f'<path d="M{cx - 25},{sh_y - 4} Q{cx},{sh_y - 12} {cx + 25},{sh_y - 4} L{cx + 19},{hip_y - 6} '
              f'L{cx - 19},{hip_y - 6} Z" fill="{pal["shirt"]}"/>'
            + f'<path d="M{cx - 20},{hip_y - 10} L{cx + 20},{hip_y - 10} L{cx + 21},{hip_y + 6} L{cx - 21},{hip_y + 6} Z" fill="{pal["shorts"]}"/>')


# ---------- scenery ----------

def ground():
    return f'<rect x="14" y="{GROUND_Y + 6}" width="290" height="3" rx="1.5" fill="#e6e3dc"/>'


def wall(x, top, width):
    return (f'<rect x="{x}" y="{top}" width="{width}" height="{GROUND_Y + 6 - top}" rx="3" fill="{PROP}"/>'
            f'<rect x="{x}" y="{top}" width="{width}" height="6" rx="3" fill="{PROP_DARK}"/>')


def tree(x):
    return (f'<rect x="{x}" y="96" width="16" height="{GROUND_Y + 6 - 96}" rx="5" fill="{PROP_DARK}"/>'
            f'<circle cx="{x + 8}" cy="70" r="36" fill="{LEAF}"/><circle cx="{x - 14}" cy="88" r="22" fill="{LEAF}"/>')


def red(p, q, r1, r2):
    return capsule(p, q, r1, r2, MUSCLE, 0.75)


# ---------- anatomy panel: the same runner, neutral, standing ----------

def standing(view, highlight, name):
    pal = NEUTRAL
    cx, sh_y, hip_y = 440, 92, 160
    out = []
    for s in (-1, 1):
        hip, knee, ankle = (cx + 10 * s, hip_y), (cx + 11 * s, 212), (cx + 11 * s, 258)
        out.append(leg(hip, knee, ankle, (cx + 15 * s, 262), pal))
    out.append(torso_front(cx, sh_y, hip_y, pal))
    for s in (-1, 1):
        out.append(arm((cx + 24 * s, sh_y), (cx + 30 * s, 132), (cx + 32 * s, 166), pal))
    out.append(head_front((cx, 62), pal, back=(view == "back")))
    out.append(highlight)
    lx, ly, tx, ty = name["leader"]
    out.append(f'<line x1="{lx}" y1="{ly}" x2="{tx}" y2="{ty}" stroke="{TEXT}" stroke-width="1"/>')
    anchor = "end" if tx < cx else "start"
    dx = -5 if tx < cx else 5
    for i, row in enumerate(name["text"]):
        out.append(text(tx + dx, ty + 4 + 15 * i, row, 13, anchor, "650" if i == 0 else "400", TEXT if i == 0 else MUTED))
    out.append(text(cx, 296, "vista " + ("frontale" if view == "front" else "posteriore"), 11, "middle", color=MUTED))
    return "".join(out)


def svg(title, scene, anat):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{title}">'
            f'<rect width="{W}" height="{H}" rx="14" fill="{BG}"/>'
            f'<line x1="320" y1="24" x2="320" y2="{H - 24}" stroke="#eeece6" stroke-width="1"/>'
            f"{scene}{anat}</svg>\n")


# ---------- exercises ----------

def quadriceps():
    """Front view, like a classic standing quad stretch: right foot held behind."""
    p, cx, sh_y, hip_y = ACTIVE, 150, 96, 164
    c = [ground()]
    # bent leg (viewer's right): thigh down, shin folded behind it, foot up by the hip
    bh, bk = (cx + 11, hip_y), (cx + 13, 214)
    foot = (cx + 31, 176)
    c.append(capsule(bk, foot, 8, 6, p["skin_far"]))                           # shin folded up behind the thigh
    c.append(capsule(foot, (cx + 33, 150), 6.5, 5.5, p["shoe"]))               # foot held by the hand
    c.append(capsule(bh, bk, 12, 8.5, p["skin"]) + capsule(bh, lerp(bh, bk, 0.5), 13.5, 11.5, p["shorts"]))
    c.append(red(lerp(bh, bk, 0.5), lerp(bh, bk, 0.92), 8, 6.5))
    # standing leg
    c.append(leg((cx - 10, hip_y), (cx - 11, 216), (cx - 11, 258), (cx - 13, 263), p))
    c.append(torso_front(cx, sh_y, hip_y, p))
    c.append(arm((cx - 24, sh_y), (cx - 34, 134), (cx - 36, 166), p))          # free arm, slightly out
    c.append(arm((cx + 24, sh_y), (cx + 40, 126), (cx + 34, 156), p))          # hand on the foot
    c.append(head_front((cx, 64), p))
    a = standing("front", red((430, 176), (429, 206), 10, 8),
                 {"leader": (418, 190, 376, 190), "text": ["Quadricipite", "davanti alla coscia"]})
    return svg("Stretching del quadricipite in piedi", "".join(c), a)


def hamstrings():
    p = ACTIVE
    hip, sh, hd = (108, 160), (150, 108), (166, 86)
    c = [ground(), wall(196, 190, 100)]
    c.append(arm(sh, (162, 140), (176, 166), p, far=True))
    c.append(leg(hip, (106, 212), (106, 256), (122, 262), p, far=True))       # standing leg
    knee, ankle = (160, 174), (214, 182)
    c.append(leg(hip, knee, ankle, (218, 166), p))                             # heel on the wall, toes up
    c.append(red(lerp(hip, knee, 0.45), lerp(hip, knee, 0.95), 7, 6).replace("<g", '<g transform="translate(1,6)"', 1))
    c.append(torso_side(hip, sh, p))
    c.append(head_side(hd, 1, p))
    c.append(arm(sh, (168, 138), (184, 164), p))
    a = standing("back", red((430, 178), (429, 208), 10, 8),
                 {"leader": (418, 192, 376, 192), "text": ["Femorali", "dietro alla coscia"]})
    return svg("Stretching dei femorali con il tallone sul muretto", "".join(c), a)


def calf_pose(back_knee, back_ankle, hip, sh, hd, highlight_t):
    p = ACTIVE
    c = [ground(), wall(226, 50, 26)]
    c.append(arm(sh, (206, sh[1] + 14), (222, sh[1] + 6), p, far=True))
    c.append(leg(hip, (hip[0] + 30, hip[1] + 50), (hip[0] + 30, 256), (hip[0] + 46, 262), p, far=True))  # front leg
    c.append(leg(hip, back_knee, back_ankle, (back_ankle[0] + 17, 262), p))                              # back leg
    c.append(red(lerp(back_knee, back_ankle, highlight_t[0]), lerp(back_knee, back_ankle, highlight_t[1]), 7.5, 6))
    c.append(torso_side(hip, sh, p))
    c.append(head_side(hd, 1, p))
    c.append(arm(sh, (202, sh[1] + 18), (220, sh[1] + 10), p))
    return "".join(c)


def calf():
    scene = calf_pose((112, 206), (88, 256), (140, 154), (184, 100), (198, 78), (0.08, 0.6))
    a = standing("back", red((429, 216), (429, 236), 8.5, 7),
                 {"leader": (418, 226, 376, 226), "text": ["Gastrocnemio", "polpaccio, gamba tesa"]})
    return svg("Stretching del polpaccio al muro, gamba dietro tesa", scene, a)


def soleus():
    scene = calf_pose((124, 214), (108, 256), (148, 164), (190, 110), (204, 88), (0.45, 0.95))
    a = standing("back", red((429, 236), (429, 252), 7, 6),
                 {"leader": (418, 244, 376, 244), "text": ["Soleo", "polpaccio basso"]})
    return svg("Stretching del soleo al muro, ginocchio dietro piegato", scene, a)


def hip():
    p = ACTIVE
    hip_j, sh, hd = (104, 156), (146, 104), (162, 82)
    c = [ground(), wall(132, 182, 150)]
    knee, ankle = (204, 168), (150, 172)
    c.append(arm(sh, (166, 134), (186, 156), p, far=True))
    c.append(capsule(knee, ankle, 8, 6, p["skin_far"]) + capsule(ankle, (138, 168), 6.5, 5, p["shoe_far"]))  # shin across the wall
    c.append(leg(hip_j, (102, 210), (102, 256), (118, 262), p))                # standing leg
    c.append(capsule(hip_j, knee, 12, 8.5, p["skin"]) + capsule(hip_j, lerp(hip_j, knee, 0.45), 13.5, 11.5, p["shorts"]))
    c.append(torso_side(hip_j, sh, p))
    c.append(red((97, 160), (90, 150), 11, 9))                                 # glute
    c.append(head_side(hd, 1, p))
    c.append(arm(sh, (172, 132), (196, 158), p))
    a = standing("back", red((431, 160), (431, 164), 12, 12),
                 {"leader": (418, 162, 376, 150), "text": ["Gluteo e piriforme", "esterno dell'anca"]})
    return svg("Stretching dell'anca con la gamba piegata sul muretto", "".join(c), a)


def upper_body_front(behind, front, highlight):
    """Front-view runner standing still; behind = arms drawn before the head, front = after it."""
    p, cx, sh_y, hip_y = ACTIVE, 150, 96, 164
    c = [ground()]
    for s in (-1, 1):
        c.append(leg((cx + 10 * s, hip_y), (cx + 11 * s, 216), (cx + 11 * s, 258), (cx + 14 * s, 263), p))
    c.append(torso_front(cx, sh_y, hip_y, p))
    for a in behind:
        c.append(arm(*a, p, far=True))
    c.append(head_front((cx, 64), p))
    for a in front:
        c.append(arm(*a, p))
    c.append(highlight)
    return "".join(c)


def cross_body():
    scene = upper_body_front(
        behind=[],
        front=[((174, 96), (142, 104), (106, 104)),           # stretched arm across the chest
               ((126, 96), (122, 132), (150, 108))],          # other forearm presses above the elbow
        highlight=red((176, 94), (170, 92), 10, 9))
    a = standing("back", red((416, 94), (414, 98), 9, 8),
                 {"leader": (406, 96, 376, 110), "text": ["Deltoide posteriore", "dietro alla spalla"]})
    return svg("Cross body stretch: braccio teso davanti al petto", scene, a)


def triceps():
    elbow = (172, 40)
    scene = upper_body_front(
        behind=[((174, 96), elbow, (150, 66))],                # forearm drops behind the head
        front=[((126, 96), (116, 58), (166, 38))],             # other hand on the raised elbow
        highlight=capsule((174, 96), elbow, 7.5, 6, ACTIVE["skin"]) + red(lerp((174, 96), elbow, 0.2), lerp((174, 96), elbow, 0.85), 7, 6))
    a = standing("back", red((413, 104), (411, 126), 7, 6),
                 {"leader": (404, 116, 376, 130), "text": ["Tricipite", "dietro al braccio"]})
    return svg("Stretching del tricipite dietro la testa", scene, a)


FIGURES = {
    "quadricipite": quadriceps, "femorali": hamstrings, "polpaccio": calf, "soleo": soleus,
    "anca": hip, "cross-body": cross_body, "tricipite": triceps,
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, draw in FIGURES.items():
        (OUT / f"{name}.svg").write_text(draw(), encoding="utf-8")
    print(f"Wrote {len(FIGURES)} figures to {OUT}")


if __name__ == "__main__":
    main()
