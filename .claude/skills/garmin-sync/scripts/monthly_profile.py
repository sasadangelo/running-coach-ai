#!/usr/bin/env python3
"""Build the month-by-month runner profile from the metric logs in health-log/.

No Garmin calls: it reads the tables written by the other calculate_*.py
scripts and summarises each metric per calendar month:

- ES, CS (best of the month): resistenza aerobica, capacita aerobica
- threshold pace, VO2max, EF, M, RES (median of the month)

Every metric is also turned into an index where 100 is its first month with
data, so metrics in different units can be compared; for threshold pace,
where lower is better, the index is inverted. Writes
health-log/monthly-profile.md and an SVG radar of the last two months to
health-log/monthly-profile.svg (embedded by the dashboard).

Usage:
    python3 .claude/skills/garmin-sync/scripts/monthly_profile.py
"""

import argparse
import math
import sys
import re
import statistics
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from calculate_decoupling import markdown_table  # noqa: E402

HEALTH_LOG = Path("health-log")
MONTHS_IT = ["", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio",
             "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]


def pace_to_sec(text: str) -> float | None:
    m = re.match(r"(\d+):(\d{2})", text)
    return int(m.group(1)) * 60 + int(m.group(2)) if m else None


def number(text: str) -> float | None:
    m = re.match(r"-?[\d.]+", text.strip())
    return float(m.group(0)) if m else None


# key, label, quality, source file, column, parser, aggregate, higher is better, display format
METRICS = [
    ("es", "ES", "Resistenza aerobica", "endurance-score.md", "ES", number, max, True, "{:.1f}"),
    ("cs", "CS", "Capacita aerobica", "capacity-score.md", "CS", number, max, True, "{:.1f}"),
    ("thr", "Soglia", "Potenza aerobica", "threshold.md", "Passo di soglia", pace_to_sec, statistics.median, False, None),
    ("vo2", "VO2max", "VO2max", "vo2max.md", "VO2max stimato", number, statistics.median, True, "{:.1f}"),
    ("ef", "EF", "Economia (cuore)", "running-economy.md", "EF (m/battito)", number, statistics.median, True, "{:.3f}"),
    ("m", "M", "Economia (meccanica)", "running-economy.md", "M", number, statistics.median, True, "{:.3f}"),
    ("res", "RES", "Economia (totale)", "running-economy.md", "RES", number, statistics.median, True, "{:.1f}"),
]
RADAR_KEYS = ["es", "cs", "thr", "vo2", "ef", "m"]  # RES left out: it is EF x M


def read_table(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows, headers = [], None
    for line in path.read_text().splitlines():
        if not line.startswith("|"):
            headers = None if not rows else headers
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells[0] == "Data":
            headers = cells
        elif headers and not set(cells[0]) <= {"-"}:
            rows.append(dict(zip(headers, cells)))
    return rows


def collect() -> dict[str, dict[tuple[int, int], list[float]]]:
    data = {key: defaultdict(list) for key, *_ in METRICS}
    for key, _label, _quality, filename, column, parse, *_ in METRICS:
        for row in read_table(HEALTH_LOG / filename):
            value = parse(row.get(column, "")) if row.get(column) else None
            if value is None:
                continue
            d = date.fromisoformat(row["Data"])
            data[key][(d.year, d.month)].append(value)
    return data


def fmt_value(metric, value: float | None) -> str:
    if value is None:
        return "n/d"
    if metric[0] == "thr":
        s = round(value)
        return f"{s // 60}:{s % 60:02d}/km"
    return metric[8].format(value)


def summarise(data):
    months = sorted({m for per_month in data.values() for m in per_month})
    table = {}
    for metric in METRICS:
        key, aggregate, higher = metric[0], metric[6], metric[7]
        values = {m: aggregate(v) for m, v in data[key].items()}
        base = values[min(values)] if values else None
        for m in months:
            v = values.get(m)
            idx = None
            if v is not None and base:
                idx = (v / base if higher else base / v) * 100
            table[(key, m)] = (v, idx)
    return months, table


def month_label(m: tuple[int, int], today: date) -> str:
    label = f"{MONTHS_IT[m[1]]} {m[0]}"
    return label + " (in corso)" if (today.year, today.month) == m else label


def radar_svg(months, table, today: date) -> str:
    size, cx, cy, r_max = 420, 240, 205, 150
    lo, hi = 80, 140  # index range on the radial axis
    shown = months[-2:]
    colors = {shown[-1]: "#33ff33"}
    if len(shown) == 2:
        colors[shown[0]] = "#5aaa5a"
    n = len(RADAR_KEYS)
    labels = {m[0]: m[1] for m in METRICS}

    def point(i, idx):
        a = -math.pi / 2 + 2 * math.pi * i / n  # i may be fractional (ring labels sit between axes)
        r = r_max * (min(max(idx, lo), hi) - lo) / (hi - lo)
        return cx + r * math.cos(a), cy + r * math.sin(a)

    out = [f'<svg viewBox="0 0 {size + 60} {size + 20}" class="w-full h-auto" style="max-width:520px" xmlns="http://www.w3.org/2000/svg" '
           f'role="img" aria-label="Profilo del runner, indice 100 = primo mese">']
    for ring in (80, 100, 120, 140):
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (point(i, ring) for i in range(n)))
        dash = "" if ring == 100 else ' stroke-dasharray="3,3"'
        out.append(f'<polygon points="{pts}" fill="none" stroke="#1a7a1a" stroke-width="{1.5 if ring == 100 else 0.7}"{dash}/>')
        x, y = point(0.5, ring)
        out.append(f'<text x="{x + 3:.1f}" y="{y - 2:.1f}" fill="#5aaa5a" font-family="Courier New" font-size="10">{ring}</text>')
    for i, key in enumerate(RADAR_KEYS):
        x, y = point(i, hi)
        out.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#1a7a1a" stroke-width="0.7"/>')
        lx, ly = point(i, hi + 13)
        anchor = "middle" if abs(lx - cx) < 10 else ("start" if lx > cx else "end")
        has_data = any(table[(key, m)][1] is not None for m in shown)
        text = labels[key] if has_data else f"{labels[key]} (n/d)"
        color = "#66ff66" if has_data else "#5aaa5a"
        out.append(f'<text x="{lx:.1f}" y="{ly + 4:.1f}" text-anchor="{anchor}" fill="{color}" font-family="Courier New" font-size="12">{text}</text>')
    for m in shown:
        pts = []
        for i, key in enumerate(RADAR_KEYS):
            _v, idx = table[(key, m)]
            pts.append((i, idx))
        valid = [(i, idx) for i, idx in pts if idx is not None]
        if len(valid) >= 3:
            poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in (point(i, idx) for i, idx in valid))
            out.append(f'<polygon points="{poly}" fill="{colors[m]}" fill-opacity="0.12" stroke="{colors[m]}" stroke-width="2"/>')
        for i, idx in valid:
            x, y = point(i, idx)
            key = RADAR_KEYS[i]
            metric = next(mt for mt in METRICS if mt[0] == key)
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{colors[m]}" stroke="#0f0f0f" stroke-width="2">'
                       f'<title>{month_label(m, today)} · {labels[key]}: {fmt_value(metric, table[(key, m)][0])} (indice {idx:.0f})</title></circle>')
    lx = 20
    for m in shown:
        out.append(f'<rect x="{lx}" y="{size + 4}" width="14" height="10" fill="{colors[m]}" rx="2"/>')
        out.append(f'<text x="{lx + 19}" y="{size + 13}" fill="#66ff66" font-family="Courier New" font-size="12">{month_label(m, today)}</text>')
        lx += 230
    out.append("</svg>")
    return "\n".join(out)


def write_markdown(path: Path, months, table, today: date) -> None:
    head = ["Qualita", "Metrica"] + [month_label(m, today) for m in months]
    lines = [
        "# Profilo mensile del runner",
        "",
        "Valore del mese e, tra parentesi, indice con **100 = primo mese con dati** (per il passo di soglia l'indice e invertito: piu alto = piu veloce). "
        "ES e CS: migliore del mese; le altre metriche: mediana del mese. n/d = nessuna misura valida nel mese.",
        "",
    ]
    rows = []
    for metric in METRICS:
        key, label, quality = metric[0], metric[1], metric[2]
        cells = []
        for m in months:
            v, idx = table[(key, m)]
            cells.append("n/d" if v is None else f"{fmt_value(metric, v)} ({idx:.0f})")
        rows.append([quality, label, *cells])
    lines += [
        *markdown_table(head, rows),
        "",
        "Le metriche si muovono a velocita diverse: ES, EF e meccanica in settimane, soglia in 4-6 settimane, VO2max in mesi. "
        "Il mese in corso e parziale. Il CS compare dal primo Tempo continuo di almeno 20' (S13).",
        "",
    ]
    path.write_text("\n".join(lines))


def parse_args():
    parser = argparse.ArgumentParser(description="Month-by-month runner profile from the metric logs")
    parser.add_argument("--logs-dir", default="training-log", help="Unused; accepted for a uniform sync call")
    return parser.parse_args()


def main() -> int:
    parse_args()
    today = date.today()
    months, table = summarise(collect())
    if not months:
        print("No metric data yet.")
        return 0
    write_markdown(HEALTH_LOG / "monthly-profile.md", months, table, today)
    (HEALTH_LOG / "monthly-profile.svg").write_text(radar_svg(months, table, today))
    print(f"Logged {len(months)} months to health-log/monthly-profile.md and monthly-profile.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
