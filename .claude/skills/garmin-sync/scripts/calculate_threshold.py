#!/usr/bin/env python3
"""Track the threshold pace (pace at the threshold HR) from Tempo sessions and races.

Threshold HR itself barely moves with fitness, so it is read from
.claude/training-zones.yaml (heart_rate.threshold) and only re-checked at races.
What this script follows is the *pace* at that HR, which is what improves.

Tempo sessions (name contains "tempo"):
  - steady samples only: 30s-smoothed speed within STEADY_TOLERANCE of its mean
    over the trailing STEADY_WINDOW_SECONDS, past the first WARMUP_SECONDS;
  - only samples faster than BLOCK_PACE_LIMIT_SEC_KM (the work itself, not the
    warm-up, cool-down or jog recoveries, where HR stays high after the effort)
    and with HR within HR_BAND of the threshold HR, so nothing is extrapolated
    from easy running;
  - each sample's speed is scaled to the threshold HR assuming speed grows
    linearly with %HRR (the same ACSM + Swain relation as calculate_vo2max.py):
        v_threshold = v * (HR_thr - HR_rest) / (HR - HR_rest)
    which is a correction of a few seconds at most inside HR_BAND;
  - the session's estimate is the median. A session whose longest continuous
    block lasts at least CONTINUOUS_BLOCK_MINUTES is labelled "Tempo continuo";
    shorter reps are labelled "Tempo a ripetute" and read as optimistic,
    because HR has not settled by the end of a 5-9 minute rep.

Races (Garmin event type "race", or a name containing "gara" / "race"), at
least RACE_MIN_MINUTES long:
  - Friel threshold HR = average HR from minute 10 to the end (race adrenaline
    adds a couple of beats);
  - Daniels VDOT from distance and time, and threshold pace at 88% of VDOT.

Nothing is changed automatically: plan paces and zones are updated by decision.

Usage:
    python3 .claude/skills/garmin-sync/scripts/calculate_threshold.py
"""

import argparse
import math
import os
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from calculate_capacity_score import BLOCK_PACE_LIMIT_SEC_KM, longest_block, smooth_speed  # noqa: E402
from calculate_decoupling import find_activity, login, markdown_table  # noqa: E402
from calculate_endurance_score import DEFAULT_LOGS_DIR, pace_str, parse_logged_runs  # noqa: E402
from calculate_vo2max import ZONES_CONFIG, extract_samples, rolling_mean  # noqa: E402

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    import yaml
except ImportError:
    yaml = None

DEFAULT_OUTPUT = "health-log/threshold.md"
WARMUP_SECONDS = 300
STEADY_WINDOW_SECONDS = 120
STEADY_TOLERANCE = 0.06
HR_BAND = 6
MIN_SAMPLES = 120
CONTINUOUS_BLOCK_MINUTES = 12  # S9 test block 2000m ~12.5 min; 1500m reps (~9-10 min) stay "a ripetute"
RACE_MIN_MINUTES = 20
RACE_KEYWORDS = ("gara", "race")
FRIEL_SKIP_SECONDS = 600


def load_config(path: str) -> tuple[float, float]:
    """(threshold HR, resting HR) from the zones config."""
    if yaml is None:
        raise SystemExit("Missing dependency 'PyYAML'. Install it with: pip install pyyaml")
    hr = yaml.safe_load(Path(path).read_text())["heart_rate"]
    return float(hr.get("threshold", 165)), float(hr["resting_average"])


def vdot(distance_m: float, minutes: float) -> float:
    v = distance_m / minutes
    vo2 = -4.60 + 0.182258 * v + 0.000104 * v * v
    pct = 0.8 + 0.1894393 * math.exp(-0.012778 * minutes) + 0.2989558 * math.exp(-0.1932605 * minutes)
    return vo2 / pct


def speed_at_vo2(vo2: float) -> float:
    """Inverse of Daniels' oxygen-cost curve, in m/s."""
    a, b, c = 0.000104, 0.182258, -4.60 - vo2
    return (-b + math.sqrt(b * b - 4 * a * c)) / (2 * a) / 60


def tempo_estimate(samples: list[tuple[float, float, float]], hr_thr: float, hr_rest: float) -> dict | None:
    smoothed = rolling_mean(samples, 15)
    speeds = []
    window_start = 0
    for i, (t, hr, _speed) in enumerate(samples):
        while samples[window_start][0] < t - STEADY_WINDOW_SECONDS:
            window_start += 1
        if t < WARMUP_SECONDS or abs(hr - hr_thr) > HR_BAND or hr <= hr_rest:
            continue
        if smoothed[i] < 1000 / BLOCK_PACE_LIMIT_SEC_KM:
            continue
        window = smoothed[window_start:i + 1]
        mean = sum(window) / len(window)
        if min(window) < mean * (1 - STEADY_TOLERANCE) or max(window) > mean * (1 + STEADY_TOLERANCE):
            continue
        speeds.append(smoothed[i] * (hr_thr - hr_rest) / (hr - hr_rest))
    if len(speeds) < MIN_SAMPLES:
        return None

    block = longest_block(samples, smooth_speed(samples))
    block_minutes = 0 if block is None else (samples[block[1]][0] - samples[block[0]][0]) / 60
    return {
        "source": "Tempo continuo" if block_minutes >= CONTINUOUS_BLOCK_MINUTES else "Tempo a ripetute",
        "minutes": len(speeds) / 60,
        "speed": statistics.median(speeds),
        "hr": None,
        "vdot": None,
    }


def race_estimate(samples: list[tuple[float, float, float]], distance_km: float) -> dict | None:
    minutes = samples[-1][0] / 60
    if minutes < RACE_MIN_MINUTES:
        return None
    late = [s[1] for s in samples if s[0] >= FRIEL_SKIP_SECONDS]
    race_vdot = vdot(distance_km * 1000, minutes)
    return {
        "source": "Gara",
        "minutes": minutes,
        "speed": speed_at_vo2(0.88 * race_vdot),
        "hr": statistics.mean(late),
        "vdot": race_vdot,
    }


def is_race(activity: dict, name: str) -> bool:
    event = (activity.get("eventType") or {}).get("typeKey", "")
    return event == "race" or any(k in name.lower() for k in RACE_KEYWORDS)


def write_log(path: Path, results: list[dict], hr_thr: float) -> None:
    headers = ["Data", "Attivita", "Fonte", "Minuti usati", "Passo di soglia", "FC di soglia (Friel)", "VDOT"]
    rows = [[
        r["date"].isoformat(),
        r["name"],
        r["source"],
        f"{r['minutes']:.0f}",
        pace_str(r["speed"]),
        "-" if r["hr"] is None else f"{r['hr']:.0f} bpm",
        "-" if r["vdot"] is None else f"{r['vdot']:.1f}",
    ] for r in results]

    def latest(source: str) -> dict | None:
        found = [r for r in results if r["source"] == source]
        return found[-1] if found else None

    summary = []
    for source, note in (("Gara", "la misura piu affidabile"),
                         ("Tempo continuo", "misura quasi diretta"),
                         ("Tempo a ripetute", "ottimista: la FC non si stabilizza in frazioni brevi")):
        r = latest(source)
        if r:
            extra = f", FC di soglia {r['hr']:.0f} bpm, VDOT {r['vdot']:.1f}" if r["hr"] is not None else ""
            summary.append(f"- **Ultima stima da {source.lower()}** ({r['date'].strftime('%d/%m')}): **{pace_str(r['speed'])}**{extra} — {note}.")
    lines = [
        "# Threshold Log",
        "",
        f"Passo di soglia: il passo sostenibile alla FC di soglia, oggi {hr_thr:.0f} bpm (`.claude/training-zones.yaml`, da verificare a ogni gara).",
        "",
        *(summary or ["Nessuna stima ancora."]),
        "",
        f"- **Tempo:** solo i tratti di lavoro (sotto {pace_str(1000 / BLOCK_PACE_LIMIT_SEC_KM)}) a passo stabile e con la FC entro +/-{HR_BAND} bpm dalla soglia; ogni campione e riportato alla FC di soglia "
        f"con la relazione lineare velocita-%FCR. Con un blocco continuo di almeno {CONTINUOUS_BLOCK_MINUTES}' la seduta conta come \"Tempo continuo\".",
        f"- **Gare** (almeno {RACE_MIN_MINUTES}'): FC media dal 10' alla fine (Friel; in gara 2-3 battiti piu alta che in un test) e passo di soglia "
        "all'88% del VDOT (Daniels).",
        "- **Nessuna modifica automatica:** le fasce del piano si aggiornano dopo una gara o quando la stima si sposta di 5-10\" in modo stabile su 2-3 sedute.",
        "",
        *(markdown_table(headers, rows) if rows else ["Nessuna seduta utilizzabile finora."]),
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def parse_args():
    parser = argparse.ArgumentParser(description="Track threshold pace from Tempo sessions and races")
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

    hr_thr, hr_rest = load_config(args.config)
    token_dir = os.path.expanduser(os.getenv("GARMINTOKENS") or "~/.garmin-running-coach-tokens")
    client = login(email, password, token_dir)

    results = []
    for run in parse_logged_runs(args.logs_dir):
        name = run["name"]
        tempo = "tempo" in name.lower()
        try:
            activity = find_activity(client, run["date"].isoformat(), name)
        except ValueError:
            continue
        race = is_race(activity, name)
        if not tempo and not race:
            continue
        samples = extract_samples(client, activity["activityId"])
        estimate = race_estimate(samples, run["distance_km"]) if race else tempo_estimate(samples, hr_thr, hr_rest)
        if estimate is None:
            print(f"{run['date']} {name}: dati insufficienti")
            continue
        r = {**run, **estimate}
        results.append(r)
        extra = f", FC Friel {r['hr']:.0f}, VDOT {r['vdot']:.1f}" if r["hr"] is not None else ""
        print(f"{r['date']} {name}: {r['source']} -> soglia {pace_str(r['speed'])} ({r['minutes']:.0f} min{extra})")

    write_log(Path(args.output), results, hr_thr)
    print(f"Logged to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
