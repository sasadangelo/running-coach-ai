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
Each run gets the median of its samples, but a single run is noisy (2 bpm of
day-to-day HR drift move it by ~1 point), so the logged VO2max is not that
value: each run updates a time-decayed mean weighted by steady minutes (time
constant TREND_TAU_DAYS), as Garmin does. A 36-minute long run moves it more
than a Tempo with 12 usable minutes, and older runs fade out. The current
estimate is the value after the last run; the median of the single-run values
in the last CURRENT_WINDOW_DAYS days is kept as a cross-check.

HR_max comes from .claude/training-zones.yaml. HR_rest is the one of the run's
own week (mean resting HR of the 7 days up to the run, from daily-health.md,
nights without sleep data excluded), so past runs don't shift when today's
resting HR changes; the YAML value is the fallback when there are fewer than
MIN_RESTING_DAYS readings. The estimate is only as good as the configured HR
max. ACSM assumes average running economy:
a less economical runner is slightly underestimated. Treat it as a trend, with
an absolute error of a few ml/kg/min; a field test (e.g. 7-minute test) or a
lab CPET is the independent check.

Usage:
    python3 .claude/skills/garmin-sync/scripts/calculate_vo2max.py
"""

import argparse
import math
import os
import re
import statistics
import sys
from datetime import date, timedelta
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
DAILY_HEALTH = "health-log/daily-health.md"
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
TREND_TAU_DAYS = 21
RESTING_WINDOW_DAYS = 7
MIN_RESTING_DAYS = 3
ROW_RE = re.compile(r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*([^|]*?)\s*\|")


def load_daily_resting(path: str) -> dict[date, float]:
    """Resting HR per day from daily-health.md, skipping nights without sleep data.

    Without the watch overnight Garmin reports the daytime minimum, which runs higher.
    """
    file = Path(path)
    if not file.exists():
        return {}
    resting, no_sleep, section = {}, set(), None
    for line in file.read_text().splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        match = ROW_RE.match(line)
        if not match:
            continue
        day, value = date.fromisoformat(match.group(1)), match.group(2)
        if section == "Recovery" and value.split()[0].replace(".", "").isdigit():
            resting[day] = float(value.split()[0])
        elif section == "Sleep" and value.startswith("N/A"):
            no_sleep.add(day)
    return {d: v for d, v in resting.items() if d not in no_sleep}


def resting_for(day: date, daily: dict[date, float], fallback: float) -> float:
    values = [daily[d] for d in (day - timedelta(days=i) for i in range(RESTING_WINDOW_DAYS)) if d in daily]
    return statistics.mean(values) if len(values) >= MIN_RESTING_DAYS else fallback


def add_trend(results: list[dict]) -> None:
    """Time-decayed mean weighted by steady minutes, stored as r["trend"]."""
    weighted = weight = 0.0
    previous = None
    for r in results:
        if previous is not None:
            decay = math.exp(-(r["date"] - previous).days / TREND_TAU_DAYS)
            weighted, weight = weighted * decay, weight * decay
        weighted += r["steady_minutes"] * r["vo2max"]
        weight += r["steady_minutes"]
        r["trend"] = weighted / weight
        previous = r["date"]


def garmin_precise_vo2max(client, day: date) -> float | None:
    """Garmin's one-decimal VO2max for the day (the activity summary only has the rounded value)."""
    try:
        metrics = client.get_max_metrics(day.isoformat())
    except Exception:
        return None
    for entry in metrics if isinstance(metrics, list) else [metrics]:
        value = ((entry or {}).get("generic") or {}).get("vo2MaxPreciseValue")
        if value is not None:
            return float(value)
    return None


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


def write_log(path: Path, results: list[dict], median: float | None, hr_max: float) -> None:
    headers = ["Data", "Attivita", "Minuti stabili", "Passo medio (GAP)", "FC media", "FC riposo", "VO2max stimato", "VO2max Garmin"]
    rows = [[
        r["date"].isoformat(),
        r["name"],
        f"{r['steady_minutes']:.0f}",
        pace_str(r["speed"]),
        f"{r['hr']:.0f} bpm",
        f"{r['hr_rest']:.1f}",
        f"{r['trend']:.1f}",
        "n/d" if r["garmin"] is None else f"{r['garmin']:.1f}",
    ] for r in results]
    if results:
        last = results[-1]
        # dVO2max/dHR from Swain: (VO2max - 3.5) / (HR - HR_rest) points per bpm.
        sensitivity = (last["vo2max"] - 3.5) / (last["hr"] - last["hr_rest"])
        median_text = f"mediana delle singole corse degli ultimi {CURRENT_WINDOW_DAYS} giorni {median:.1f}" if median is not None else "nessuna corsa negli ultimi 28 giorni"
        current_line = (f"**Stima attuale: {last['trend']:.1f} ml/kg/min** (al {last['date'].isoformat()}; "
                        f"controllo: {median_text}).")
        noise_line = (f"- **Perche non si usa la singola corsa:** con i valori dell'ultima corsa 1 bpm di FC vale {sensitivity:.2f} punti, "
                      f"quindi 2 bpm di variazione giornaliera (sonno, stress, caldo, sensore) sposterebbero la stima di ~{2 * sensitivity:.1f}, "
                      "mentre il VO2max vero cambia in settimane o mesi.")
    else:
        current_line, noise_line = "Nessuna corsa con abbastanza tratti stabili.", ""
    lines = [
        "# VO2max Log",
        "",
        current_line,
        "",
        f"Stima dalla relazione FC-passo: `VO2 = 0.2 x velocita (m/min) + 3.5` (ACSM, corsa in piano, velocita corretta per la pendenza), "
        f"`%FCR = (FC - FC riposo) / ({hr_max:.0f} - FC riposo)`, `VO2max = 3.5 + (VO2 - 3.5) / %FCR` (Swain).",
        "",
        f"- **VO2max stimato:** ogni corsa aggiorna la stima senza sostituirla, come fa Garmin. E la media delle stime delle corse fatte fin li, "
        f"pesata sui minuti stabili e sull'eta: il peso di una corsa si dimezza ogni {TREND_TAU_DAYS * math.log(2):.0f} giorni "
        f"(costante di tempo {TREND_TAU_DAYS} giorni). Un lungo da 36' sposta la stima tre volte piu di un Tempo con 12' utili. "
        "La stima attuale e quella dopo l'ultima corsa.",
        *([noise_line] if noise_line else []),
        f"- **Tratti usati:** solo ritmo stabile (passo entro +/-{STEADY_TOLERANCE * 100:.0f}% per almeno {STEADY_WINDOW_SECONDS // 60} minuti), "
        f"FC stabile (oscillazione massima {MAX_HR_SWING} bpm), dopo i primi {WARMUP_SECONDS // 60} minuti e con FC sopra il {MIN_HRR * 100:.0f}% della riserva. "
        f"Recuperi, transizioni, defaticamenti dopo lavori intensi e ripetute brevi restano esclusi, cosi come le corse con piu del {MAX_WALK_FRACTION * 100:.0f}% di camminata.",
        f"- **Per corsa:** mediana dei tratti stabili; servono almeno {MIN_SAMPLES // 60} minuti stabili.",
        f"- **FC max {hr_max:.0f}** da `.claude/training-zones.yaml`: la stima dipende soprattutto dalla FC max. "
        f"**FC a riposo** della settimana della corsa (media dei {RESTING_WINDOW_DAYS} giorni fino alla corsa da `daily-health.md`, notti senza orologio escluse): "
        "cosi le corse passate non cambiano quando cambia la FC a riposo di oggi.",
        "- **Limiti:** la formula ACSM presume un'economia di corsa media; caldo, poco sonno e stanchezza alzano la FC e abbassano la stima. Da leggere come trend; l'errore sul valore assoluto e di qualche punto. "
        "Verifica indipendente: test dei 7' (VO2max ~ 3.5 x VAM in km/h) o test cardiopolmonare.",
        "- **VO2max Garmin:** valore con un decimale del giorno della corsa (metriche giornaliere Garmin; se manca, quello intero dell'attivita). "
        "Calcolato da Garmin con la sua FC max (194 nel profilo Garmin), quindi tendenzialmente piu alto.",
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
    parser.add_argument("--daily-health", default=DAILY_HEALTH)
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

    hr_max, fallback_rest = load_hr_config(args.config)
    daily_resting = load_daily_resting(args.daily_health)
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
        hr_rest = resting_for(run["date"], daily_resting, fallback_rest)
        estimates = steady_estimates(samples, hr_max, hr_rest)
        if len(estimates) < MIN_SAMPLES:
            continue
        r = {
            **run,
            "hr_rest": hr_rest,
            "steady_minutes": len(estimates) / 60,
            "vo2max": statistics.median(e[0] for e in estimates),
            "speed": statistics.mean(e[1] for e in estimates),
            "hr": statistics.mean(e[2] for e in estimates),
            "garmin": garmin_precise_vo2max(client, run["date"]) or activity.get("vO2MaxValue"),
        }
        results.append(r)
        print(f"{r['date']} {r['name']}: VO2max singola corsa {r['vo2max']:.1f} ({r['steady_minutes']:.0f} min stabili, "
              f"{pace_str(r['speed'])} @ {r['hr']:.0f} bpm, riposo {hr_rest:.1f}; Garmin {r['garmin']})")

    median = None
    if results:
        add_trend(results)
        cutoff = results[-1]["date"] - timedelta(days=CURRENT_WINDOW_DAYS)
        recent = [r["vo2max"] for r in results if r["date"] > cutoff]
        median = statistics.median(recent) if recent else None
        for r in results:
            print(f"{r['date']} {r['name']}: VO2max stimato {r['trend']:.1f}")
        print(f"Current estimate: {results[-1]['trend']:.1f} (median of {len(recent)} single runs in {CURRENT_WINDOW_DAYS} days: {median:.1f})")

    write_log(Path(args.output), results, median, hr_max)
    print(f"Logged to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
