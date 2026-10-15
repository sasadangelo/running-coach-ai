#!/usr/bin/env python3
"""Compute the Capacity Score (CS) for every Tempo run with a continuous
threshold block of at least MIN_BLOCK_MINUTES.

CS = (speed_m_s / HR) * block_minutes * 100 * C * M_drift

Only the threshold block counts: warm-up, cool-down and anything outside the
longest continuous stretch faster than BLOCK_PACE_LIMIT_SEC_KM are left out.
Interval sessions (reps with recoveries) never reach MIN_BLOCK_MINUTES of
continuous effort, so they get no CS.

- speed / HR: efficiency factor over the block minus its first LAG_SECONDS
  (at threshold HR needs 1-2 minutes to catch up with pace).
- block_minutes: duration of the whole continuous block.
- C (pace control) = share of the analysed block whose 30s-smoothed pace sits
  inside the Tempo band (TEMPO_BAND_SEC_KM): starting too fast and fading, or
  slowing out of the band, both lower it.
- M_drift = 1.0 if the pace:HR decoupling between the two halves of the
  analysed block is <= 5%, else max(0.5, 1 - (dec - 5) / 100).

Each scored session gets a "**CS**:" line in training-log/week-N.md, and the
full breakdown goes to health-log/capacity-score.md.

Usage:
    python3 .claude/skills/garmin-sync/scripts/calculate_capacity_score.py
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from calculate_decoupling import extract_series, find_activity, login, markdown_table  # noqa: E402
from calculate_endurance_score import (  # noqa: E402
    DEFAULT_LOGS_DIR,
    annotate_week_logs,
    decoupling_multiplier,
    pace_str,
    parse_logged_runs,
)

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

DEFAULT_OUTPUT = "health-log/capacity-score.md"
CS_LINE_PREFIX = "**CS**:"
MIN_BLOCK_MINUTES = 20
BLOCK_PACE_LIMIT_SEC_KM = 400  # 6:40/km: faster than warm-up/cool-down (7:10-7:50), slower than any Tempo pace
MAX_GAP_SECONDS = 20  # brief dips below the limit (a bend, a crossing) don't split the block
LAG_SECONDS = 120
SMOOTHING_SECONDS = 30
TEMPO_BAND_SEC_KM = (370, 390)  # 6:10-6:30/km, the plan's continuous Tempo band (revised 15 Oct)

# (upper bound, name, typical continuous threshold block, description). The bounds
# assume roughly 1.6-2 CS per minute at threshold: a more efficient runner moves
# up with fewer minutes.
LEVELS = [
    (35, "Soglia iniziale", "20-22 min", "Primo blocco continuo a soglia: lo sforzo regge, ma e al limite della durata."),
    (45, "Soglia in crescita", "22-28 min", "Il blocco si allunga senza crollare di passo; la FC resta governabile."),
    (60, "Soglia consolidata", "28-35 min", "Mezz'ora a soglia in controllo: la base del Tempo classico da 10K."),
    (75, "Soglia avanzata", "35-45 min", "Blocchi lunghi con deriva contenuta: capacita aerobica da 10K forte o mezza."),
    (100, "Soglia esperta", "45-60 min", "Quasi un'ora vicino alla soglia: livello da mezza maratona competitiva."),
    (float("inf"), "Elite", "> 60 min", "Oltre l'ora a soglia con FC stabile: ritmo gara da mezza di alto livello."),
]


def level_rows() -> list[list[str]]:
    rows = []
    lower = 0
    for upper, name, minutes, description in LEVELS:
        bounds = f">= {lower}" if upper == float("inf") else f"{lower}-{upper}"
        rows.append([name, bounds, minutes, description])
        lower = upper
    return rows


def level(score: float) -> str:
    return next(name for limit, name, _minutes, _description in LEVELS if score < limit)


def smooth_speed(series: list[tuple[float, float, float]]) -> list[float]:
    """Centered rolling mean of speed over SMOOTHING_SECONDS (by elapsed time, not sample count)."""
    half = SMOOTHING_SECONDS / 2
    smoothed = []
    lo = hi = 0
    total = 0.0
    for t, _hr, _speed in series:
        while hi < len(series) and series[hi][0] <= t + half:
            total += series[hi][2]
            hi += 1
        while series[lo][0] < t - half:
            total -= series[lo][2]
            lo += 1
        smoothed.append(total / (hi - lo))
    return smoothed


def longest_block(series: list[tuple[float, float, float]], smoothed: list[float]) -> tuple[int, int] | None:
    """Indices [start, end] of the longest stretch faster than BLOCK_PACE_LIMIT_SEC_KM, gaps <= MAX_GAP_SECONDS bridged."""
    limit_speed = 1000 / BLOCK_PACE_LIMIT_SEC_KM
    best = None
    start = last_fast = None
    for i, speed in enumerate(smoothed):
        if speed < limit_speed:
            continue
        if start is None or series[i][0] - series[last_fast][0] > MAX_GAP_SECONDS:
            start = i
        last_fast = i
        if best is None or series[i][0] - series[start][0] > series[best[1]][0] - series[best[0]][0]:
            best = (start, i)
    return best


def score_block(series: list[tuple[float, float, float]]) -> dict | None:
    """CS components for the longest threshold block, or None if it is shorter than MIN_BLOCK_MINUTES."""
    smoothed = smooth_speed(series)
    block = longest_block(series, smoothed)
    if block is None:
        return None
    start, end = block
    block_minutes = (series[end][0] - series[start][0]) / 60
    if block_minutes < MIN_BLOCK_MINUTES:
        return {"block_minutes": block_minutes, "cs": None}

    analysed = [i for i in range(start, end + 1) if series[i][0] >= series[start][0] + LAG_SECONDS]
    mid = series[analysed[0]][0] + (series[analysed[-1]][0] - series[analysed[0]][0]) / 2

    def avg(indices: list[int], col: int) -> float:
        return sum(series[i][col] for i in indices) / len(indices)

    hr, speed = avg(analysed, 1), avg(analysed, 2)
    first = [i for i in analysed if series[i][0] <= mid]
    second = [i for i in analysed if series[i][0] > mid]
    ef1 = avg(first, 2) / avg(first, 1)
    ef2 = avg(second, 2) / avg(second, 1)
    decoupling_pct = (ef1 - ef2) / ef1 * 100

    fast_band, slow_band = (1000 / sec for sec in TEMPO_BAND_SEC_KM)
    in_band = sum(1 for i in analysed if slow_band <= smoothed[i] <= fast_band) / len(analysed)

    m_drift = decoupling_multiplier(decoupling_pct)
    base = speed / hr * block_minutes * 100
    return {
        "block_minutes": block_minutes, "speed": speed, "hr": hr,
        "decoupling_pct": decoupling_pct, "m_drift": m_drift, "c": in_band,
        "base": base, "cs": base * in_band * m_drift,
    }


def write_log(path: Path, results: list[dict]) -> None:
    headers = ["Data", "Attivita", "Blocco", "Passo blocco", "FC blocco", "C (in fascia)",
               "Decoupling", "M_drift", "Base", "CS", "Livello"]
    rows = [[
        r["date"].isoformat(),
        r["name"],
        f"{r['block_minutes']:.1f} min",
        pace_str(r["speed"]),
        f"{r['hr']:.0f} bpm",
        f"{r['c'] * 100:.0f}%",
        f"{r['decoupling_pct']:.1f}%",
        f"{r['m_drift']:.2f}",
        f"{r['base']:.1f}",
        f"{r['cs']:.1f}",
        level(r["cs"]),
    ] for r in results]

    band = "-".join(pace_str(1000 / sec).removesuffix("/km") for sec in TEMPO_BAND_SEC_KM)
    lines = [
        "# Capacity Score Log",
        "",
        "Score di capacita aerobica dei Tempo run: `CS = (velocita m/s / FC) x minuti di blocco x 100 x C x M_drift`.",
        "",
        f"- **Blocco**: il tratto continuo piu lungo sotto {pace_str(1000 / BLOCK_PACE_LIMIT_SEC_KM)}; riscaldamento e defaticamento esclusi. Solo blocchi di almeno {MIN_BLOCK_MINUTES} minuti: le sedute a ripetute non hanno CS.",
        f"- **Passo e FC del blocco**: medie del blocco senza i primi {LAG_SECONDS // 60} minuti, in cui la FC sta ancora salendo.",
        f"- **C (controllo del passo)**: quota del blocco corsa nella fascia Tempo {band}/km (passo medio su {SMOOTHING_SECONDS}s).",
        "- **M_drift (deriva)**: decoupling passo:FC tra prima e seconda meta del blocco; 1.0 se <= 5%, altrimenti 1 - (decoupling - 5)/100.",
        "- **Da guardare oltre al CS**: la FC del blocco a parita di passo. Se scende nelle settimane, la capacita aerobica sta migliorando.",
        "",
        "## Categorie",
        "",
        *markdown_table(["Livello", "CS", "Blocco continuo a soglia", "Capacita aerobica"], level_rows()),
        "",
        "Le durate indicative valgono per circa 1.6-2 punti di CS al minuto: chi e piu efficiente, cioe piu veloce a parita di FC, sale di livello con meno minuti.",
        "",
        "## Tempo run",
        "",
        *(markdown_table(headers, rows) if rows else [f"Nessun Tempo con un blocco continuo di almeno {MIN_BLOCK_MINUTES} minuti finora."]),
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def parse_args():
    parser = argparse.ArgumentParser(description="Compute the Capacity Score of every Tempo run with a long enough continuous block")
    parser.add_argument("--logs-dir", default=DEFAULT_LOGS_DIR)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if load_dotenv:
        load_dotenv(Path(__file__).resolve().parent.parent / ".env")
        load_dotenv()
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    if not email or not password:
        print("Set GARMIN_EMAIL and GARMIN_PASSWORD before running this script.", file=sys.stderr)
        return 1

    tempos = [r for r in parse_logged_runs(args.logs_dir) if "tempo" in r["name"].lower()]
    token_dir = os.path.expanduser(os.getenv("GARMINTOKENS") or "~/.garmin-running-coach-tokens")
    client = login(email, password, token_dir)

    scored = []
    for run in tempos:
        activity = find_activity(client, run["date"].isoformat(), run["name"])
        block = score_block(extract_series(client, activity["activityId"]))
        if block is None or block["cs"] is None:
            minutes = 0 if block is None else block["block_minutes"]
            print(f"{run['date']} {run['name']}: blocco continuo piu lungo {minutes:.1f} min - nessun CS")
            scored.append({**run, "cs": None})
            continue
        r = {**run, **block}
        scored.append(r)
        print(f"{r['date']} {r['name']}: CS {r['cs']:.1f} ({level(r['cs'])}) - blocco {r['block_minutes']:.1f} min, "
              f"{pace_str(r['speed'])} @ {r['hr']:.0f} bpm, C {r['c']:.2f}, dec {r['decoupling_pct']:.1f}%")

    write_log(Path(args.output), [r for r in scored if r["cs"] is not None])
    annotate_week_logs(args.logs_dir, scored, CS_LINE_PREFIX, "cs", lambda v: f"{v:.1f} ({level(v)})")
    print(f"Logged to {args.output} and {args.logs_dir}/week-*.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
