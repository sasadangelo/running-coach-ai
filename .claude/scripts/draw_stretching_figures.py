#!/usr/bin/env python3
"""Draw the figures of teoria/10-stretching-al-parco.md.

One SVG per exercise, two panels side by side:
- left: a cartoon of the pose (side or front view), with the props found in a
  park (wall, low wall, tree) and the stretched muscle drawn in red on the body;
- right: a simple anatomical figure (front or back view) with the same muscle
  highlighted and labelled.

The figures are deliberately schematic: they show the position of the body
and where the stretch should be felt, not anatomical detail.

Usage:
    python3 .claude/scripts/draw_stretching_figures.py
"""

from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "teoria" / "img" / "10-stretching"

BODY = "#3b4a5c"      # cartoon body
BODY_BACK = "#7d8b9c"  # limbs on the far side of the body
MUSCLE = "#d64545"     # stretched muscle
PROP = "#c9b79c"       # wall, low wall, tree
GROUND = "#9a9a92"
SKIN = "#e8e4dc"       # anatomy silhouette
SKIN_EDGE = "#b9b3a6"
TEXT = "#3a3a36"
BG = "#fbfaf7"
FONT = 'font-family="system-ui, -apple-system, Segoe UI, Roboto, sans-serif"'

W, H = 540, 300
GROUND_Y = 262


def line(p, q, color, width, opacity=1.0):
    return (f'<line x1="{p[0]}" y1="{p[1]}" x2="{q[0]}" y2="{q[1]}" stroke="{color}" '
            f'stroke-width="{width}" stroke-linecap="round" opacity="{opacity}"/>')


def limb(points, color, width):
    return "".join(line(a, b, color, width) for a, b in zip(points, points[1:]))


def part(p, q, t0, t1):
    """The piece of segment p-q between fractions t0 and t1."""
    return ((p[0] + (q[0] - p[0]) * t0, p[1] + (q[1] - p[1]) * t0),
            (p[0] + (q[0] - p[0]) * t1, p[1] + (q[1] - p[1]) * t1))


def head(c, r=15):
    return f'<circle cx="{c[0]}" cy="{c[1]}" r="{r}" fill="{BODY}"/>'


def shoe(ankle, forward=1):
    x, y = ankle
    return f'<ellipse cx="{x + 7 * forward}" cy="{y + 4}" rx="11" ry="5" fill="{BODY}"/>'


def ground():
    return line((10, GROUND_Y + 8), (300, GROUND_Y + 8), GROUND, 2)


def wall(x, top, width=26):
    return f'<rect x="{x}" y="{top}" width="{width}" height="{GROUND_Y + 8 - top}" rx="3" fill="{PROP}"/>'


def tree(x):
    return (f'<rect x="{x}" y="70" width="18" height="{GROUND_Y + 8 - 70}" rx="6" fill="{PROP}"/>'
            f'<circle cx="{x + 9}" cy="58" r="34" fill="#a9c49a" opacity="0.8"/>')


def label(x, y, text, size=13, anchor="start", weight="400", color=TEXT):
    return f'<text x="{x}" y="{y}" {FONT} font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{text}</text>'


# ---------- anatomy panel ----------

def anatomy(view, highlights, name):
    """Silhouette centred at x=430; highlights are (kind, data) drawn in red; name is the label."""
    cx = 430
    out = [label(cx, 290, "vista " + ("frontale" if view == "front" else "posteriore"), 11, "middle", color="#77766f")]
    sk = lambda p, q, w: line(p, q, SKIN_EDGE, w + 3) + line(p, q, SKIN, w)  # noqa: E731
    # legs
    for s in (-1, 1):
        hip, knee, ankle = (cx + 12 * s, 158), (cx + 14 * s, 212), (cx + 13 * s, 262)
        out.append(sk(hip, knee, 20) + sk(knee, ankle, 15))
    # arms
    for s in (-1, 1):
        sh, el, wr = (cx + 34 * s, 72), (cx + 42 * s, 120), (cx + 46 * s, 160)
        out.append(sk(sh, el, 13) + sk(el, wr, 11))
    # torso and head
    out.append(f'<path d="M{cx - 36},64 Q{cx},56 {cx + 36},64 L{cx + 26},135 Q{cx + 30},160 {cx + 24},165 '
               f'L{cx - 24},165 Q{cx - 30},160 {cx - 26},135 Z" fill="{SKIN}" stroke="{SKIN_EDGE}" stroke-width="1.5"/>')
    out.append(f'<rect x="{cx - 7}" y="44" width="14" height="16" fill="{SKIN}" stroke="{SKIN_EDGE}" stroke-width="1.5"/>')
    out.append(f'<circle cx="{cx}" cy="36" r="16" fill="{SKIN}" stroke="{SKIN_EDGE}" stroke-width="1.5"/>')
    if view == "back":
        out.append(line((cx, 70), (cx, 155), SKIN_EDGE, 1))
    for kind, data in highlights:
        if kind == "seg":
            p, q, w = data
            out.append(line(p, q, MUSCLE, w, 0.85))
        elif kind == "ell":
            x, y, rx, ry = data
            out.append(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{MUSCLE}" opacity="0.85"/>')
    lx, ly, tx, ty = name["leader"]
    out.append(line((lx, ly), (tx, ty), TEXT, 1))
    for i, row in enumerate(name["text"]):
        out.append(label(tx + (4 if tx > cx else -4), ty + 4 + 15 * i, row, 13, "start" if tx > cx else "end", "600" if i == 0 else "400"))
    return "".join(out)


def svg(title, cartoon, anat):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{title}">'
            f'<rect width="{W}" height="{H}" rx="12" fill="{BG}"/>'
            f'<line x1="318" y1="20" x2="318" y2="{H - 20}" stroke="#e2e1dc" stroke-width="1"/>'
            f"{cartoon}{anat}</svg>\n")


# ---------- exercises ----------
# Cartoon convention: side view facing right unless stated; far-side limbs drawn first in BODY_BACK.

def quadriceps():
    hip, sh = (140, 150), (142, 88)
    stand = [hip, (142, 205), (142, GROUND_Y)]
    bent_knee, bent_ankle = (138, 208), (112, 158)
    c = [ground(), tree(214)]
    c.append(limb([sh, (168, 108), (212, 104)], BODY_BACK, 11))           # far arm on the tree
    c.append(limb(stand, BODY, 15) + shoe(stand[-1]))
    c.append(limb([hip, bent_knee, bent_ankle], BODY, 15))
    c.append(line(*part(hip, bent_knee, 0.12, 0.88), MUSCLE, 9))          # front of the thigh
    c.append(f'<ellipse cx="{bent_ankle[0] - 4}" cy="{bent_ankle[1] - 6}" rx="6" ry="10" fill="{BODY}"/>')
    c.append(line(hip, sh, BODY, 26) + head((146, 64)))
    c.append(limb([sh, (122, 122), (114, 156)], BODY, 11))                # hand on the ankle
    a = anatomy("front", [("seg", ((418, 162), (416, 204), 14))],
                {"leader": (412, 182, 360, 182), "text": ["Quadricipite", "(davanti alla coscia)"]})
    return svg("Stretching del quadricipite in piedi", "".join(c), a)


def hamstrings():
    hip, sh = (110, 160), (150, 104)
    stand = [hip, (108, 212), (108, GROUND_Y)]
    knee, heel = (160, 172), (214, 180)
    c = [ground(), wall(206, 184, 90)]
    c.append(limb(stand, BODY_BACK, 15) + shoe(stand[-1]))
    c.append(limb([hip, knee, heel], BODY, 15) + f'<ellipse cx="{heel[0] + 6}" cy="{heel[1] - 4}" rx="6" ry="10" fill="{BODY}"/>')
    c.append(line(*part(hip, knee, 0.1, 0.9), MUSCLE, 7).replace(f'y1="{hip[1]}', f'y1="{hip[1]}'))
    c[-1] = line((hip[0] + 6, hip[1] + 7), (knee[0] - 3, knee[1] + 7), MUSCLE, 6)  # back of the thigh, underside
    c.append(line(hip, sh, BODY, 26) + head((166, 86)))
    c.append(limb([sh, (170, 134), (180, 166)], BODY, 11))                # hands toward the shin
    a = anatomy("back", [("seg", ((418, 162), (416, 204), 14))],
                {"leader": (412, 184, 360, 184), "text": ["Femorali", "(dietro alla coscia)"]})
    return svg("Stretching dei femorali con il tallone sul muretto", "".join(c), a)


def calf():
    hip, sh = (140, 150), (186, 96)
    front = [hip, (172, 200), (172, GROUND_Y)]
    back = [hip, (112, 206), (88, GROUND_Y)]
    c = [ground(), wall(222, 40)]
    c.append(limb(front, BODY_BACK, 15) + shoe(front[-1]))
    c.append(limb(back, BODY, 15) + shoe(back[-1]))
    c.append(line(*part(back[1], back[2], 0.1, 0.65), MUSCLE, 9))        # upper calf of the straight leg
    c.append(line(hip, sh, BODY, 26) + head((196, 72)))
    c.append(limb([sh, (206, 112), (220, 104)], BODY, 11))
    a = anatomy("back", [("seg", ((416, 214), (416, 236), 13))],
                {"leader": (410, 224, 360, 224), "text": ["Gastrocnemio", "(polpaccio, gamba tesa)"]})
    return svg("Stretching del polpaccio al muro, gamba dietro tesa", "".join(c), a)


def soleus():
    hip, sh = (146, 160), (188, 104)
    front = [hip, (176, 206), (176, GROUND_Y)]
    back = [hip, (122, 214), (108, GROUND_Y)]
    c = [ground(), wall(222, 40)]
    c.append(limb(front, BODY_BACK, 15) + shoe(front[-1]))
    c.append(limb(back, BODY, 15) + shoe(back[-1]))
    c.append(line(*part(back[1], back[2], 0.45, 0.92), MUSCLE, 9))       # low calf, bent knee
    c.append(line(hip, sh, BODY, 26) + head((197, 80)))
    c.append(limb([sh, (207, 118), (220, 110)], BODY, 11))
    a = anatomy("back", [("seg", ((417, 232), (418, 254), 10))],
                {"leader": (412, 244, 360, 244), "text": ["Soleo", "(polpaccio basso)"]})
    return svg("Stretching del soleo al muro, ginocchio dietro piegato", "".join(c), a)


def hip():
    hip_j, sh = (106, 150), (150, 98)
    stand = [hip_j, (104, 206), (104, GROUND_Y)]
    knee, ankle = (204, 160), (150, 166)
    c = [ground(), wall(128, 172, 150)]
    c.append(limb(stand, BODY, 15) + shoe(stand[-1]))
    c.append(line(knee, ankle, BODY_BACK, 13))                            # shin lying across the low wall
    c.append(line(hip_j, knee, BODY, 16))
    c.append(f'<ellipse cx="{hip_j[0] - 4}" cy="{hip_j[1] + 2}" rx="13" ry="12" fill="{MUSCLE}" opacity="0.9"/>')  # glute
    c.append(line(hip_j, sh, BODY, 26) + head((164, 78)))
    c.append(limb([sh, (176, 126), (196, 150)], BODY, 11))                # hands on the knee
    a = anatomy("back", [("ell", (418, 152, 13, 11))],
                {"leader": (406, 150, 360, 140), "text": ["Gluteo e piriforme", "(esterno dell'anca)"]})
    return svg("Stretching dell'anca con la gamba piegata sul muretto", "".join(c), a)


def front_figure(arms, highlight, behind=()):
    """Front-view cartoon: legs, torso and head, then the given arm polylines."""
    cx = 150
    c = [ground()]
    for s in (-1, 1):
        c.append(limb([(cx + 13 * s, 160), (cx + 14 * s, 212), (cx + 14 * s, GROUND_Y)], BODY, 15))
        c.append(f'<ellipse cx="{cx + 16 * s}" cy="{GROUND_Y + 4}" rx="10" ry="5" fill="{BODY}"/>')
    c.append(f'<path d="M{cx - 30},82 Q{cx},74 {cx + 30},82 L{cx + 22},160 L{cx - 22},160 Z" fill="{BODY}"/>')
    for pts, color in behind:       # limbs passing behind the head
        c.append(limb(pts, color, 12))
    c.append(head((cx, 56), 17))
    for pts, color in arms:
        c.append(limb(pts, color, 12))
    c.append(highlight)
    return "".join(c)


def cross_body():
    l_sh, r_sh = (124, 88), (176, 88)
    stretched = [r_sh, (152, 98), (102, 98)]           # right arm straight across the chest
    helper = [l_sh, (120, 128), (150, 104)]            # left forearm presses above the elbow
    hl = f'<ellipse cx="{r_sh[0] + 4}" cy="{r_sh[1] - 2}" rx="11" ry="9" fill="{MUSCLE}" opacity="0.9"/>'
    c = front_figure([(stretched, BODY_BACK), (helper, BODY)], hl)
    a = anatomy("back", [("ell", (397, 70, 10, 9))],
                {"leader": (388, 72, 360, 96), "text": ["Deltoide posteriore", "(dietro alla spalla)"]})
    return svg("Cross body stretch: braccio teso davanti al petto", c, a)


def triceps():
    l_sh, r_sh = (124, 88), (176, 88)
    elbow = (178, 28)
    upper = [r_sh, elbow]                               # right upper arm straight up
    forearm = [elbow, (150, 62)]                        # forearm drops behind the head
    helper = [l_sh, (120, 50), (172, 30)]               # left hand over the head, on the right elbow
    hl = line(*part(r_sh, elbow, 0.15, 0.85), MUSCLE, 9)
    c = front_figure([(upper, BODY), (helper, BODY)], hl, behind=[(forearm, BODY_BACK)])
    a = anatomy("back", [("seg", ((395, 80), (389, 112), 9))],
                {"leader": (386, 96, 360, 120), "text": ["Tricipite", "(dietro al braccio)"]})
    return svg("Stretching del tricipite dietro la testa", c, a)


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
