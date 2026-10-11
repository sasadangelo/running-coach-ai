#!/usr/bin/env python3
"""Compute the Endurance Score (ES) for every long run logged so far.

ES = (speed_m_s / HR_avg) * distance_km * 100 * C * M_dec * H

- speed_m_s / HR_avg: efficiency factor (metres per heartbeat-second); the x100
  brings the score onto a readable scale.
- C (continuity) = (run_time / total_time)^2 * max(0.2, 1 - 0.05 * n_stops).
  A stop is a walk segment of at least MIN_STOP_SECONDS below running speed;
  shorter dips (traffic lights, GPS noise) are ignored.
- M_dec (aerobic drift) = 1.0 if decoupling <= 5%, else max(0.5, 1 - (dec - 5) / 100).
  Decoupling comes from calculate_decoupling.compute_decoupling (10-min warm-up
  excluded, >= 20 min left to analyse). When it can't be computed (too short or
  too much walking) the run gets no ES at all: assuming no drift would make the
  score look better than what was measured. The run still counts for H.
- H (recency) = days since the last long run covering >= 85% of this distance:
  <= 14 -> 1.0, 15-30 -> 0.90, > 30 or never -> 0.75.

Long runs are the Sunday runs in training-log/ (excluding strides), or the
dates passed with --date. Besides the summary in health-log/endurance-score.md,
each long run's section in training-log/week-N.md gets "**Decoupling**:" and
"**ES**:" lines, and its decoupling is recorded in health-log/aerobic-decoupling.md
(re-running replaces all of them, so it is safe after every garmin_sync).

Usage:
    python3 .claude/skills/garmin-sync/scripts/calculate_endurance_score.py
    python3 .claude/skills/garmin-sync/scripts/calculate_endurance_score.py --date 2026-10-18
"""

import argparse
import glob
import os
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from calculate_decoupling import (  # noqa: E402
    WALK_SPEED_THRESHOLD_M_S,
    compute_decoupling,
    extract_series,
    find_activity,
    login,
    markdown_table,
    update_log,
)

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

DEFAULT_LOGS_DIR = "training-log"
DEFAULT_OUTPUT = "health-log/endurance-score.md"
DECOUPLING_LOG = "health-log/aerobic-decoupling.md"
MIN_STOP_SECONDS = 15
SIMILAR_DISTANCE_RATIO = 0.85

ACTIVITY_RE = re.compile(r"^### (\d{4}-\d{2}-\d{2}) [\d:]+ - (.+)$")
DISTANCE_RE = re.compile(r"^\*\*Distance\*\*:\s*([\d.]+) km")
HR_RE = re.compile(r"^\*\*Heart Rate\*\*:\s*(\d+) bpm")
DURATION_RE = re.compile(r"^\*\*Duration\*\*:\s*(\d+):(\d+):(\d+)")
ES_LINE_PREFIX = "**ES**:"
DECOUPLING_LINE_PREFIX = "**Decoupling**:"
RUN_TIME_PREFIX = "**Run time**:"

# (upper bound, name, typical continuous long run, description). The bounds assume
# roughly 1.5-2 ES per km at easy effort: a more efficient runner (faster at the
# same HR) moves up with fewer km.
LEVELS = [
    (4, "Avvio", "< 2.5 km o corsa/cammino", "La corsa continua non regge ancora: servono camminate per arrivare in fondo."),
    (8, "Primi km", "2.5-5 km", "Corsa continua acquisita su distanze brevi; ogni km in piu e un adattamento nuovo."),
    (12, "Base", "5-7.5 km", "Oltre la mezz'ora di corsa senza fermarsi, FC stabile: e gia piu di quanto corra la gran parte delle persone."),
    (16, "Base solida", "7.5-10 km", "Vicino ai 10 km in corsa continua; la resistenza regge un'ora di sforzo."),
    (24, "10K", "10-15 km", "Il 10 km e un allenamento, non piu una gara al limite."),
    (35, "Avanzato", "15-21 km", "Lunghi oltre l'ora e mezza, deriva cardiaca contenuta."),
    (50, "Mezzamaratoneta", "21-30 km", "La mezza maratona e alla portata in allenamento; la maratona e il passo successivo."),
    (70, "Maratoneta", "30-42 km", "Lunghi da maratona con FC contenuta e decoupling sotto il 5%."),
    (float("inf"), "Elite / Ultra", "> 42 km o maratona veloce", "Volumi da ultra o lunghi molto veloci a FC bassa, in stabilita perfetta."),
]


def parse_logged_runs(logs_dir: str) -> list[dict]:
    """Return every logged activity with date, name, distance, avg HR and duration."""
    runs = []
    for path in glob.glob(str(Path(logs_dir) / "week-*.md")):
        current = None
        for line in Path(path).read_text().splitlines():
            m = ACTIVITY_RE.match(line)
            if m:
                current = {"date": date.fromisoformat(m.group(1)), "name": m.group(2).strip()}
                runs.append(current)
                continue
            if current is None:
                continue
            if m := DISTANCE_RE.match(line):
                current["distance_km"] = float(m.group(1))
            elif m := HR_RE.match(line):
                current["hr_avg"] = float(m.group(1))
            elif m := DURATION_RE.match(line):
                h, mi, s = (int(x) for x in m.groups())
                current["duration_s"] = h * 3600 + mi * 60 + s
    return sorted((r for r in runs if "distance_km" in r), key=lambda r: r["date"])


def is_long_run(run: dict) -> bool:
    return run["date"].weekday() == 6 and "allungh" not in run["name"].lower()


def extract_speed_series(client, activity_id: int) -> list[tuple[float, float]]:
    """(elapsed_seconds, speed_m_s) for every sample, stopped ones included."""
    details = client.get_activity_details(activity_id)
    index = {d["key"]: d["metricsIndex"] for d in details.get("metricDescriptors", [])}
    i_dur, i_speed = index["sumDuration"], index["directSpeed"]
    series = []
    for entry in details.get("activityDetailMetrics", []):
        values = entry.get("metrics", [])
        if values[i_dur] is None:
            continue
        series.append((values[i_dur], values[i_speed] or 0.0))
    return series


def continuity(series: list[tuple[float, float]]) -> dict:
    """Run/total time ratio and number of walk breaks lasting >= MIN_STOP_SECONDS."""
    run_s = walk_s = 0.0
    stops = 0
    segment = 0.0
    for (t0, speed), (t1, _) in zip(series, series[1:]):
        dt = t1 - t0
        if dt <= 0:
            continue
        if speed < WALK_SPEED_THRESHOLD_M_S:
            walk_s += dt
            segment += dt
        else:
            run_s += dt
            if segment >= MIN_STOP_SECONDS:
                stops += 1
            segment = 0.0
    if segment >= MIN_STOP_SECONDS:
        stops += 1
    total = run_s + walk_s
    ratio = run_s / total if total else 1.0
    return {"run_ratio": ratio, "stops": stops, "c": ratio**2 * max(0.2, 1 - 0.05 * stops)}


def decoupling_multiplier(decoupling_pct: float) -> float:
    if decoupling_pct <= 5.0:
        return 1.0
    return max(0.5, 1.0 - (decoupling_pct - 5.0) / 100.0)


def recency(run: dict, previous_longs: list[dict]) -> tuple[int | None, float]:
    similar = [p for p in previous_longs if p["distance_km"] >= SIMILAR_DISTANCE_RATIO * run["distance_km"]]
    if not similar:
        return None, 0.75
    days = (run["date"] - similar[-1]["date"]).days
    if days <= 14:
        return days, 1.0
    if days <= 30:
        return days, 0.90
    return days, 0.75


def level_rows() -> list[list[str]]:
    rows = []
    lower = 0
    for upper, name, distance, description in LEVELS:
        bounds = f">= {lower}" if upper == float("inf") else f"{lower}-{upper}"
        rows.append([name, bounds, distance, description])
        lower = upper
    return rows


def level(score: float) -> str:
    return next(name for limit, name, _distance, _description in LEVELS if score < limit)


def score_run(client, run: dict, previous_longs: list[dict]) -> dict:
    activity = find_activity(client, run["date"].isoformat(), run["name"])
    speed_series = extract_speed_series(client, activity["activityId"])
    cont = continuity(speed_series)

    try:
        decoupling = compute_decoupling(extract_series(client, activity["activityId"]))
    except ValueError:
        decoupling = None
    decoupling_pct = None if decoupling is None else decoupling["decoupling_pct"]

    days, h = recency(run, previous_longs)
    speed = run["distance_km"] * 1000 / run["duration_s"]
    base = speed / run["hr_avg"] * run["distance_km"] * 100
    m_dec = None if decoupling_pct is None else decoupling_multiplier(decoupling_pct)
    es = None if m_dec is None else base * cont["c"] * m_dec * h
    return {**run, **cont, "speed": speed, "base": base, "decoupling": decoupling, "decoupling_pct": decoupling_pct,
            "m_dec": m_dec, "days": days, "h": h, "es": es}


def pace_str(speed_m_s: float) -> str:
    total = round(1000 / speed_m_s)
    return f"{total // 60}:{total % 60:02d}/km"


def write_log(path: Path, results: list[dict]) -> None:
    headers = ["Data", "Attivita", "Distanza", "Passo", "FC media", "% corsa", "Stop", "C",
               "Decoupling", "M_dec", "Giorni da lungo simile", "H", "Base", "ES", "Livello"]
    rows = [[
        r["date"].isoformat(),
        r["name"],
        f"{r['distance_km']:.2f} km",
        pace_str(r["speed"]),
        f"{r['hr_avg']:.0f} bpm",
        f"{r['run_ratio'] * 100:.0f}%",
        str(r["stops"]),
        f"{r['c']:.2f}",
        "n/d" if r["decoupling_pct"] is None else f"{r['decoupling_pct']:.1f}%",
        "n/d" if r["m_dec"] is None else f"{r['m_dec']:.2f}",
        "nessuno" if r["days"] is None else str(r["days"]),
        f"{r['h']:.2f}",
        f"{r['base']:.1f}",
        "n/d" if r["es"] is None else f"{r['es']:.1f}",
        "n/d" if r["es"] is None else level(r["es"]),
    ] for r in results]

    lines = [
        "# Endurance Score Log",
        "",
        "Score di resistenza aerobica dei lunghi: `ES = (velocita m/s / FC media) x km x 100 x C x M_dec x H`.",
        "",
        f"- **C (continuita)**: (tempo di corsa / tempo totale)^2 x max(0.2, 1 - 0.05 x stop). Uno stop e una camminata di almeno {MIN_STOP_SECONDS}s sotto ~8:30/km.",
        "- **M_dec (deriva)**: 1.0 se decoupling <= 5%, altrimenti 1 - (decoupling - 5)/100. Decoupling dallo stesso calcolo di `aerobic-decoupling.md`. Quando non e calcolabile (corsa sotto i 30 min o troppo camminata) ES e n/d: senza deriva misurata lo score non e confrontabile. Il lungo conta comunque per H.",
        f"- **H (memoria)**: giorni dall'ultimo lungo di almeno l'{SIMILAR_DISTANCE_RATIO * 100:.0f}% della distanza: <= 14 -> 1.0, 15-30 -> 0.90, oltre o mai -> 0.75.",
        "",
        "## Categorie",
        "",
        *markdown_table(["Livello", "ES", "Lungo continuo tipico", "Tenuta aerobica"], level_rows()),
        "",
        "Le distanze indicative valgono a ritmo facile (circa 1.5-2 punti di ES per km): chi e piu efficiente, cioe piu veloce a parita di FC, sale di livello con meno km.",
        "",
        "## Lunghi",
        "",
        *markdown_table(headers, rows),
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def annotate_week_logs(logs_dir: str, results: list[dict], prefix: str, key: str, format_fn) -> None:
    """Write (or replace) the `prefix` line, just before "**Run time**:", in each activity's section.

    Activities in `results` whose `key` is None get the line removed.
    """
    by_key = {(r["date"].isoformat(), r["name"]): r for r in results}
    for path in glob.glob(str(Path(logs_dir) / "week-*.md")):
        text = Path(path).read_text()
        lines = text.splitlines()
        out = []
        current = None
        for line in lines:
            m = ACTIVITY_RE.match(line)
            if m:
                current = by_key.get((m.group(1), m.group(2).strip()))
            elif current and line.startswith(prefix):
                continue
            elif current and current[key] is not None and line.startswith(RUN_TIME_PREFIX):
                out.append(f"{prefix} {format_fn(current[key])}")
            out.append(line)
        if out != lines:
            Path(path).write_text("\n".join(out) + ("\n" if text.endswith("\n") else ""))


def parse_args():
    parser = argparse.ArgumentParser(description="Compute the Endurance Score of every long run")
    parser.add_argument("--date", action="append", help="YYYY-MM-DD of a long run (repeatable); default: every Sunday run in the log")
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

    runs = parse_logged_runs(args.logs_dir)
    if args.date:
        wanted = {date.fromisoformat(d) for d in args.date}
        longs = [r for r in runs if r["date"] in wanted and "allungh" not in r["name"].lower()]
    else:
        longs = [r for r in runs if is_long_run(r)]
    if not longs:
        print("No long runs found.", file=sys.stderr)
        return 1

    token_dir = os.path.expanduser(os.getenv("GARMINTOKENS") or "~/.garmin-running-coach-tokens")
    client = login(email, password, token_dir)

    results = []
    for i, run in enumerate(longs):
        r = score_run(client, run, longs[:i])
        results.append(r)
        dec = "n/d" if r["decoupling_pct"] is None else f"{r['decoupling_pct']:.1f}%"
        es = "n/d" if r["es"] is None else f"{r['es']:.1f} ({level(r['es'])})"
        print(f"{r['date']} {r['name']}: ES {es} - base {r['base']:.1f}, "
              f"C {r['c']:.2f} ({r['stops']} stop), dec {dec}, H {r['h']:.2f}")

    write_log(Path(args.output), results)
    annotate_week_logs(args.logs_dir, results, DECOUPLING_LINE_PREFIX, "decoupling_pct", lambda v: f"{v:.1f}%")
    annotate_week_logs(args.logs_dir, results, ES_LINE_PREFIX, "es", lambda v: f"{v:.1f} ({level(v)})")
    for r in results:
        if r["decoupling"] is not None:
            update_log(Path(DECOUPLING_LOG), r["date"].isoformat(), "resistenza", r["name"], r["distance_km"], r["decoupling"])
    print(f"Logged to {args.output}, {DECOUPLING_LOG} and {args.logs_dir}/week-*.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
