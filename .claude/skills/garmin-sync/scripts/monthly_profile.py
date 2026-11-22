#!/usr/bin/env python3
"""Build the month-by-month runner profile from the metric logs in health-log/.

No Garmin calls: it reads the tables written by the other calculate_*.py
scripts and summarises each metric per calendar month:

- ES, CS (best of the month): resistenza aerobica, capacita aerobica
- threshold pace, EF, M, RES (median of the month)
- VO2max (last value of the month: the logged estimate is already a smoothed mean)

Every metric is also turned into an index where 100 is its first month with
data, so metrics in different units can be compared; for threshold pace,
where lower is better, the index is inverted. Writes
health-log/monthly-profile.md and an SVG radar of the last three months (the month in progress dashed) to
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


def last(values: list[float]) -> float:
    """Last value of the month (values are in date order)."""
    return values[-1]


def number(text: str) -> float | None:
    m = re.match(r"-?[\d.]+", text.strip())
    return float(m.group(0)) if m else None


# key, label, quality, source file, column, parser, aggregate, higher is better, display format
METRICS = [
    ("es", "ES", "Resistenza aerobica", "endurance-score.md", "ES", number, max, True, "{:.1f}"),
    ("cs", "CS", "Capacita aerobica", "capacity-score.md", "CS", number, max, True, "{:.1f}"),
    ("thr", "Soglia", "Potenza aerobica", "threshold.md", "Passo di soglia", pace_to_sec, statistics.median, False, None),
    # VO2max stimato is already a time-decayed mean: a median of it only adds lag, so take the month-end value.
    ("vo2", "VO2max", "VO2max", "vo2max.md", "VO2max stimato", number, last, True, "{:.1f}"),
    ("ef", "EF", "Economia (cuore)", "running-economy.md", "EF (m/battito)", number, statistics.median, True, "{:.3f}"),
    ("m", "M", "Economia (meccanica)", "running-economy.md", "M", number, statistics.median, True, "{:.3f}"),
    ("res", "RES", "Economia (totale)", "running-economy.md", "RES", number, statistics.median, True, "{:.1f}"),
    ("fs", "FS", "Forza", "strength-mobility.md", "FS", number, statistics.median, True, "{:.0f}"),
    ("mcs", "MCS", "Mobilita e controllo", "strength-mobility.md", "MCS", number, statistics.median, True, "{:.0f}"),
]
RADAR_KEYS = ["es", "cs", "thr", "vo2", "ef", "m", "fs", "mcs"]  # RES left out: it is EF x M


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
        for row in sorted(read_table(HEALTH_LOG / filename), key=lambda r: r["Data"]):
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
    size, cx, cy, r_max = 540, 300, 262, 205
    shown = months[-3:]
    # Index range on the radial axis: 80 at the centre, outer ring at least 140 and raised
    # in steps of 20 to the highest index shown, so a metric that grows a lot (ES) isn't clipped.
    top = max((table[(k, m)][1] or 0) for k in RADAR_KEYS for m in shown)
    lo, hi = 80, max(140, math.ceil(top / 20) * 20)
    palette = ["var(--s3, #1baf7a)", "var(--s2, #eb6834)", "var(--s1, #2a78d6)"]
    colors = {m: c for m, c in zip(shown, palette[-len(shown):])}
    current = (today.year, today.month)
    grid, muted, text_col, surface = "var(--grid, #ebeae6)", "var(--text-muted, #77766f)", "var(--text-secondary, #52514e)", "var(--surface-1, #fcfcfb)"
    n = len(RADAR_KEYS)
    labels = {m[0]: m[1] for m in METRICS}

    def point(i, idx):
        a = -math.pi / 2 + 2 * math.pi * i / n  # i may be fractional (ring labels sit between axes)
        r = r_max * (min(max(idx, lo), hi) - lo) / (hi - lo)
        return cx + r * math.cos(a), cy + r * math.sin(a)

    out = [f'<svg viewBox="0 0 {size + 60} {size + 20}" style="max-width:760px;width:100%;height:auto" xmlns="http://www.w3.org/2000/svg" '
           f'role="img" aria-label="Profilo del runner, indice 100 = primo mese">']
    for ring in range(lo, hi + 1, 20):
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (point(i, ring) for i in range(n)))
        dash = "" if ring == 100 else ' stroke-dasharray="3,3"'
        out.append(f'<polygon points="{pts}" fill="none" style="stroke:{grid}" stroke-width="{1.5 if ring == 100 else 0.7}"{dash}/>')
        x, y = point(0.5, ring)
        out.append(f'<text x="{x + 3:.1f}" y="{y - 2:.1f}" style="fill:{muted}" font-size="10">{ring}</text>')
    for i, key in enumerate(RADAR_KEYS):
        x, y = point(i, hi)
        out.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" style="stroke:{grid}" stroke-width="0.7"/>')
        lx, ly = point(i, hi + 13)
        anchor = "middle" if abs(lx - cx) < 10 else ("start" if lx > cx else "end")
        has_data = any(table[(key, m)][1] is not None for m in shown)
        text = labels[key] if has_data else f"{labels[key]} (n/d)"
        color = text_col if has_data else muted
        out.append(f'<text x="{lx:.1f}" y="{ly + 4:.1f}" text-anchor="{anchor}" style="fill:{color}" font-size="12">{text}</text>')
    for m in shown:
        pts = []
        for i, key in enumerate(RADAR_KEYS):
            _v, idx = table[(key, m)]
            pts.append((i, idx))
        valid = [(i, idx) for i, idx in pts if idx is not None]
        if len(valid) >= 3:
            poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in (point(i, idx) for i, idx in valid))
            dash = ' stroke-dasharray="6,4"' if m == current else ""
            fill_op = 0.05 if m == current else 0.12
            out.append(f'<polygon points="{poly}" style="fill:{colors[m]};stroke:{colors[m]}" fill-opacity="{fill_op}" stroke-width="2"{dash}/>')
        for i, idx in valid:
            x, y = point(i, idx)
            key = RADAR_KEYS[i]
            metric = next(mt for mt in METRICS if mt[0] == key)
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" style="fill:{colors[m]};stroke:{surface}" stroke-width="2">'
                       f'<title>{month_label(m, today)} · {labels[key]}: {fmt_value(metric, table[(key, m)][0])} (indice {idx:.0f})</title></circle>')
    lx = 20
    for m in shown:
        out.append(f'<rect x="{lx}" y="{size + 4}" width="14" height="10" style="fill:{colors[m]}" rx="2"/>')
        out.append(f'<text x="{lx + 19}" y="{size + 13}" style="fill:{text_col}" font-size="12">{month_label(m, today)}</text>')
        lx += 190
    out.append("</svg>")
    return "\n".join(out)


def write_markdown(path: Path, months, table, today: date) -> None:
    head = ["Qualita", "Metrica"] + [month_label(m, today) for m in months]
    lines = [
        "# Profilo mensile del runner",
        "",
        "Valore del mese e, tra parentesi, indice con **100 = primo mese con dati** (per il passo di soglia l'indice e invertito: piu alto = piu veloce). "
        "ES e CS: migliore del mese; VO2max: ultimo valore del mese (la stima e gia una media mobile); le altre metriche: mediana del mese. n/d = nessuna misura valida nel mese.",
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
        "Il mese in corso e parziale. Il CS compare dal primo Tempo continuo di almeno 20' (S13). "
        "Forza (FS) e Mobilita e controllo (MCS) vengono dal test mensile di health-log/strength-mobility.md (primo test 24/10/2026).",
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
