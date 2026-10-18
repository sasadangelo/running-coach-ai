#!/usr/bin/env python3
"""Estimate VO2max from the heart-rate / pace relationship of every logged run.

For each steady-state sample (constant pace for at least STEADY_WINDOW_SECONDS,
past the first WARMUP_SECONDS of the run):

    VO2 at that pace (ACSM, flat)   = 0.2 * speed_m_min + 3.5
    %HRR                            = (HR - HR_rest) / (HR_max - HR_rest)
    VO2max (Swain: %HRR ~ %VO2R)    = 3.5 + (VO2 - 3.5) / %HRR

Speed is Garmin's grade-adjusted speed when available, so hills don't skew it.
Samples below MIN_HRR are dropped (the %HRR ~ %VO2R relation is least reliable
at low intensity), and so are recoveries and transitions: over the trailing
window the 30s-smoothed speed must stay within STEADY_TOLERANCE of its mean and
HR must vary by at most MAX_HR_SWING bpm (a cool-down after hard reps has a
steady pace but a falling HR). Runs with more than MAX_WALK_FRACTION of walking
(interval sessions with walked recoveries) are skipped.
Each run gets the median of its samples; the current estimate is the median
of the runs in the last CURRENT_WINDOW_DAYS days.

HR_max and HR_rest come from .claude/training-zones.yaml, so the estimate is
only as good as the configured HR max. ACSM assumes average running economy:
a less economical runner is slightly underestimated. Treat it as a trend, with
an absolute error of a few ml/kg/min; a field test (e.g. 7-minute test) or a
lab CPET is the independent check.

Usage:
    python3 .claude/skills/garmin-sync/scripts/calculate_vo2max.py
"""

import argparse
import os
import statistics
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from calculate_decoupling import find_activity, login, markdown_table  # noqa: E402
from calculate_endurance_score import DEFAULT_LOGS_DIR, pace_str, parse_logged_runs  # noqa: E402

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    import yaml
except ImportError:
    yaml = None

DEFAULT_OUTPUT = "health-log/vo2max.md"
ZONES_CONFIG = ".claude/training-zones.yaml"
WARMUP_SECONDS = 600
STEADY_WINDOW_SECONDS = 120
STEADY_TOLERANCE = 0.06
SMOOTHING_SECONDS = 30
MIN_RUNNING_SPEED_M_S = 1.85  # ~9:00/km, same running threshold as garmin_sync.py
MIN_HRR = 0.5
MAX_HR_SWING = 8
MAX_WALK_FRACTION = 0.10
MIN_SAMPLES = 300  # ~5 minutes of steady running at 1 Hz
CURRENT_WINDOW_DAYS = 28


def load_hr_config(path: str) -> tuple[float, float]:
    text = Path(path).read_text()
    if yaml:
        hr = yaml.safe_load(text)["heart_rate"]
        return float(hr["max"]), float(hr["resting_average"])
    values = {}
    for line in text.splitlines():
        key, _, value = line.strip().partition(":")
        if key in ("max", "resting_average") and value.strip():
            values[key] = float(value.split("#")[0])
    return values["max"], values["resting_average"]


def extract_samples(client, activity_id: int) -> list[tuple[float, float, float]]:
    """(elapsed_s, HR, grade-adjusted speed) samples."""
    details = client.get_activity_details(activity_id, maxchart=10000)
    index = {d["key"]: d["metricsIndex"] for d in details.get("metricDescriptors", [])}
    speed_key = "directGradeAdjustedSpeed" if "directGradeAdjustedSpeed" in index else "directSpeed"
    samples = []
    for entry in details.get("activityDetailMetrics", []):
        values = entry.get("metrics", [])
        t, hr, speed = values[index["sumDuration"]], values[index["directHeartRate"]], values[index[speed_key]]
        if t is None or hr is None or speed is None:
            continue
        samples.append((t, hr, speed))
    return samples


def rolling_mean(samples: list[tuple[float, float, float]], half_window: float) -> list[float]:
    out = []
    lo = hi = 0
    total = 0.0
    for t, _hr, _speed in samples:
        while hi < len(samples) and samples[hi][0] <= t + half_window:
            total += samples[hi][2]
            hi += 1
        while samples[lo][0] < t - half_window:
            total -= samples[lo][2]
            lo += 1
        out.append(total / (hi - lo))
    return out


def steady_estimates(samples: list[tuple[float, float, float]], hr_max: float, hr_rest: float) -> list[tuple[float, float, float]]:
    """(VO2max estimate, speed, HR) for every steady-state sample."""
    smoothed = rolling_mean(samples, SMOOTHING_SECONDS / 2)
    estimates = []
    window_start = 0
    for i, (t, hr, _speed) in enumerate(samples):
        while samples[window_start][0] < t - STEADY_WINDOW_SECONDS:
            window_start += 1
        if t < WARMUP_SECONDS or samples[window_start][0] > t - STEADY_WINDOW_SECONDS + 5:
            continue
        window = smoothed[window_start:i + 1]
        mean = sum(window) / len(window)
        if mean < MIN_RUNNING_SPEED_M_S or min(window) < mean * (1 - STEADY_TOLERANCE) or max(window) > mean * (1 + STEADY_TOLERANCE):
            continue
        window_hr = [s[1] for s in samples[window_start:i + 1]]
        if max(window_hr) - min(window_hr) > MAX_HR_SWING:
            continue
        hrr = (hr - hr_rest) / (hr_max - hr_rest)
        if hrr < MIN_HRR or hrr > 1:
            continue
        vo2 = 0.2 * smoothed[i] * 60 + 3.5
        estimates.append((3.5 + (vo2 - 3.5) / hrr, smoothed[i], hr))
    return estimates


def write_log(path: Path, results: list[dict], current: float | None, hr_max: float, hr_rest: float) -> None:
    headers = ["Data", "Attivita", "Minuti stabili", "Passo medio (GAP)", "FC media", "VO2max stimato", "VO2max Garmin"]
    rows = [[
        r["date"].isoformat(),
        r["name"],
        f"{r['steady_minutes']:.0f}",
        pace_str(r["speed"]),
        f"{r['hr']:.0f} bpm",
        f"{r['vo2max']:.1f}",
        "n/d" if r["garmin"] is None else f"{r['garmin']:.0f}",
    ] for r in results]
    current_line = (f"**Stima attuale: {current:.1f} ml/kg/min** (mediana delle corse degli ultimi {CURRENT_WINDOW_DAYS} giorni)."
                    if current is not None else f"Nessuna corsa valida negli ultimi {CURRENT_WINDOW_DAYS} giorni.")
    lines = [
        "# VO2max Log",
        "",
        current_line,
        "",
        f"Stima dalla relazione FC-passo: `VO2 = 0.2 x velocita (m/min) + 3.5` (ACSM, corsa in piano, velocita corretta per la pendenza), "
        f"`%FCR = (FC - {hr_rest:.0f}) / ({hr_max:.0f} - {hr_rest:.0f})`, `VO2max = 3.5 + (VO2 - 3.5) / %FCR` (Swain).",
        "",
        f"- **Tratti usati:** solo ritmo stabile (passo entro +/-{STEADY_TOLERANCE * 100:.0f}% per almeno {STEADY_WINDOW_SECONDS // 60} minuti), "
        f"FC stabile (oscillazione massima {MAX_HR_SWING} bpm), dopo i primi {WARMUP_SECONDS // 60} minuti e con FC sopra il {MIN_HRR * 100:.0f}% della riserva. "
        f"Recuperi, transizioni, defaticamenti dopo lavori intensi e ripetute brevi restano esclusi, cosi come le corse con piu del {MAX_WALK_FRACTION * 100:.0f}% di camminata.",
        f"- **Per corsa:** mediana dei tratti stabili; servono almeno {MIN_SAMPLES // 60} minuti stabili.",
        f"- **FC max {hr_max:.0f} e FC a riposo {hr_rest:.0f}** da `.claude/training-zones.yaml`: la stima dipende soprattutto dalla FC max.",
        "- **Limiti:** la formula ACSM presume un'economia di corsa media; caldo, poco sonno e stanchezza alzano la FC e abbassano la stima. Da leggere come trend; l'errore sul valore assoluto e di qualche punto. "
        "Verifica indipendente: test dei 7' (VO2max ~ 3.5 x VAM in km/h) o test cardiopolmonare.",
        "- **VO2max Garmin:** calcolato da Garmin con la sua FC max (194 nel profilo Garmin), quindi tendenzialmente piu alto.",
        "",
        *(markdown_table(headers, rows) if rows else ["Nessuna corsa con abbastanza tratti stabili."]),
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def parse_args():
    parser = argparse.ArgumentParser(description="Estimate VO2max from steady-state HR and pace")
    parser.add_argument("--logs-dir", default=DEFAULT_LOGS_DIR)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--config", default=ZONES_CONFIG)
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

    hr_max, hr_rest = load_hr_config(args.config)
    runs = parse_logged_runs(args.logs_dir)
    token_dir = os.path.expanduser(os.getenv("GARMINTOKENS") or "~/.garmin-running-coach-tokens")
    client = login(email, password, token_dir)

    results = []
    for run in runs:
        try:
            activity = find_activity(client, run["date"].isoformat(), run["name"])
        except ValueError:
            continue
        samples = extract_samples(client, activity["activityId"])
        walk_fraction = sum(1 for s in samples if s[2] < MIN_RUNNING_SPEED_M_S) / max(len(samples), 1)
        if walk_fraction > MAX_WALK_FRACTION:
            continue
        estimates = steady_estimates(samples, hr_max, hr_rest)
        if len(estimates) < MIN_SAMPLES:
            continue
        r = {
            **run,
            "steady_minutes": len(estimates) / 60,
            "vo2max": statistics.median(e[0] for e in estimates),
            "speed": statistics.mean(e[1] for e in estimates),
            "hr": statistics.mean(e[2] for e in estimates),
            "garmin": activity.get("vO2MaxValue"),
        }
        results.append(r)
        print(f"{r['date']} {r['name']}: VO2max {r['vo2max']:.1f} ({r['steady_minutes']:.0f} min stabili, "
              f"{pace_str(r['speed'])} @ {r['hr']:.0f} bpm; Garmin {r['garmin']})")

    current = None
    if results:
        cutoff = results[-1]["date"] - timedelta(days=CURRENT_WINDOW_DAYS)
        recent = [r["vo2max"] for r in results if r["date"] > cutoff]
        current = statistics.median(recent) if recent else None
        print(f"Current estimate: {current:.1f} (median of {len(recent)} runs)")

    write_log(Path(args.output), results, current, hr_max, hr_rest)
    print(f"Logged to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
