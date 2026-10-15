#!/usr/bin/env python3
"""Track running economy at a fixed reference pace: Efficiency Factor plus a mechanics index.

Economy metrics change a lot with speed, so everything is measured only on
samples whose 30s-smoothed pace falls inside REFERENCE_BAND_SEC_KM (the long-run
pace), past the first WARMUP_SECONDS of the run:

- EF (Efficiency Factor) = metres per heartbeat = speed_m_min / HR. Higher is
  better. It mixes aerobic fitness and economy; it cannot separate them.
- M (mechanics index) = sqrt((VR_GREEN / vertical ratio) * (GCT_GREEN / ground
  contact time)), against the upper limits of Garmin's green band. M = 1 means
  "green" mechanics, below 1 orange, above 1 blue.
- RES (Running Economy Score) = EF * 100 * M.

Runs need at least MIN_SAMPLES seconds in the band. Each long run gets an
"**Economia**:" line in its training-log/week-N.md section, and the full table
goes to health-log/running-economy.md. Heat, short sleep and fatigue raise HR
and lower EF without economy getting worse: read 4-6 week trends.

Usage:
    python3 .claude/skills/garmin-sync/scripts/calculate_economy.py
"""

import argparse
import math
import os
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from calculate_decoupling import find_activity, login, markdown_table  # noqa: E402
from calculate_endurance_score import (  # noqa: E402
    DEFAULT_LOGS_DIR,
    annotate_week_logs,
    is_long_run,
    pace_str,
    parse_logged_runs,
)
from calculate_vo2max import rolling_mean  # noqa: E402

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

DEFAULT_OUTPUT = "health-log/running-economy.md"
ECONOMY_LINE_PREFIX = "**Economia**:"
REFERENCE_BAND_SEC_KM = (420, 440)  # 7:00-7:20/km, the current long-run pace
WARMUP_SECONDS = 600
MIN_SAMPLES = 180
VR_GREEN = 8.6  # Garmin green band upper limit, vertical ratio %
GCT_GREEN = 272  # Garmin green band upper limit, ground contact time ms


def extract_samples(client, activity_id: int) -> list[dict]:
    details = client.get_activity_details(activity_id, maxchart=10000)
    index = {d["key"]: d["metricsIndex"] for d in details.get("metricDescriptors", [])}

    def get(values, key):
        return values[index[key]] if key in index else None

    samples = []
    for entry in details.get("activityDetailMetrics", []):
        values = entry.get("metrics", [])
        t, hr, speed = get(values, "sumDuration"), get(values, "directHeartRate"), get(values, "directSpeed")
        if t is None or hr is None or speed is None:
            continue
        cadence = get(values, "directDoubleCadence") or (get(values, "directRunCadence") or 0) * 2 or None
        samples.append({"t": t, "hr": hr, "speed": speed, "cadence": cadence,
                        "gct": get(values, "directGroundContactTime"), "vr": get(values, "directVerticalRatio")})
    return samples


def economy(samples: list[dict]) -> dict | None:
    smoothed = rolling_mean([(s["t"], s["hr"], s["speed"]) for s in samples], 15)
    fast, slow = (1000 / sec for sec in REFERENCE_BAND_SEC_KM)
    band = [(s, v) for s, v in zip(samples, smoothed) if s["t"] >= WARMUP_SECONDS and slow <= v <= fast]
    if len(band) < MIN_SAMPLES:
        return None

    def mean_of(key):
        values = [s[key] for s, _ in band if s[key]]
        return statistics.mean(values) if values else None

    speed = statistics.mean(v for _, v in band)
    hr = statistics.mean(s["hr"] for s, _ in band)
    ef = speed * 60 / hr
    gct, vr = mean_of("gct"), mean_of("vr")
    m = math.sqrt((VR_GREEN / vr) * (GCT_GREEN / gct)) if gct and vr else None
    return {
        "minutes": len(band) / 60, "speed": speed, "hr": hr, "ef": ef,
        "cadence": mean_of("cadence"), "gct": gct, "vr": vr, "m": m,
        "res": None if m is None else ef * 100 * m,
    }


def summary_line(r: dict) -> str:
    if r["m"] is None:
        return f"EF {r['ef']:.3f} m/battito (meccanica n/d)"
    return f"EF {r['ef']:.3f} m/battito · M {r['m']:.3f} · RES {r['res']:.1f}"


def write_log(path: Path, results: list[dict]) -> None:
    headers = ["Data", "Attivita", "Minuti in fascia", "Passo", "FC", "EF (m/battito)", "Battiti/km",
               "Cadenza", "Contatto al suolo", "Rapporto verticale", "M", "RES"]
    rows = [[
        r["date"].isoformat(),
        r["name"],
        f"{r['minutes']:.0f}",
        pace_str(r["speed"]),
        f"{r['hr']:.0f} bpm",
        f"{r['ef']:.3f}",
        f"{1000 / r['ef']:.0f}",
        "n/d" if r["cadence"] is None else f"{r['cadence']:.0f} spm",
        "n/d" if r["gct"] is None else f"{r['gct']:.0f} ms",
        "n/d" if r["vr"] is None else f"{r['vr']:.2f}%",
        "n/d" if r["m"] is None else f"{r['m']:.3f}",
        "n/d" if r["res"] is None else f"{r['res']:.1f}",
    ] for r in results]
    band = "-".join(pace_str(1000 / sec).removesuffix("/km") for sec in REFERENCE_BAND_SEC_KM)
    lines = [
        "# Running Economy Log",
        "",
        f"Economia di corsa a passo fisso: solo i tratti a {band}/km (passo medio su 30s), esclusi i primi {WARMUP_SECONDS // 60} minuti.",
        "",
        "- **EF (Efficiency Factor)** = metri per battito (velocita in m/min / FC). Piu alto e meglio. Somma forma aerobica ed economia: da solo non le separa.",
        f"- **M (indice meccanico)** = radice di (({VR_GREEN} / rapporto verticale) x ({GCT_GREEN} / contatto al suolo)), rispetto ai limiti della fascia verde Garmin. "
        "1 = meccanica verde, sotto 1 arancione, sopra 1 blu. Se EF e M salgono insieme, migliora anche l'economia.",
        "- **RES (Running Economy Score)** = EF x 100 x M.",
        "- **Lettura:** caldo, poco sonno e stanchezza alzano la FC e abbassano l'EF senza che l'economia sia peggiorata. Contano i trend di 4-6 settimane. "
        "La fascia di passo va aggiornata se il passo del lungo cambia molto, altrimenti i confronti si fanno su pochi minuti.",
        "",
        *(markdown_table(headers, rows) if rows else ["Nessuna corsa con abbastanza minuti nella fascia di riferimento."]),
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def parse_args():
    parser = argparse.ArgumentParser(description="Track running economy (EF + mechanics) at a fixed reference pace")
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

    token_dir = os.path.expanduser(os.getenv("GARMINTOKENS") or "~/.garmin-running-coach-tokens")
    client = login(email, password, token_dir)

    longs = [r for r in parse_logged_runs(args.logs_dir) if is_long_run(r)]
    results = []
    for run in longs:
        try:
            activity = find_activity(client, run["date"].isoformat(), run["name"])
        except ValueError:
            continue
        e = economy(extract_samples(client, activity["activityId"]))
        if e is None:
            print(f"{run['date']} {run['name']}: troppo pochi minuti nella fascia di riferimento")
            results.append({**run, "line": None})
            continue
        r = {**run, **e}
        r["line"] = summary_line(r)
        results.append(r)
        print(f"{r['date']} {r['name']}: {r['line']}")

    write_log(Path(args.output), [r for r in results if r["line"] is not None])
    annotate_week_logs(args.logs_dir, results, ECONOMY_LINE_PREFIX, "line", lambda v: v)
    print(f"Logged to {args.output} and {args.logs_dir}/week-*.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
