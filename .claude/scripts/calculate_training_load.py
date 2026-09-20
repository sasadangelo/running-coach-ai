#!/usr/bin/env python3
"""
Calculate CTL (Chronic Training Load / "fitness"), ATL (Acute Training Load /
"fatigue") and TSB (Training Stress Balance / "form"), TrainingPeaks-style,
from the per-activity TSS values already logged in training-log/week-*.md by
garmin_sync.py (NGP-based IF -> TSS).

CTL = 42-day exponentially weighted moving average of daily TSS
ATL = 7-day exponentially weighted moving average of daily TSS
TSB = yesterday's CTL - yesterday's ATL (the "form" going into a given day,
      before that day's own training stress is applied)

Usage:
    python3 .claude/scripts/calculate_training_load.py
    python3 .claude/scripts/calculate_training_load.py --logs-dir training-log --output health-log/training-load.md
"""

import argparse
import glob
import re
from datetime import date, timedelta
from pathlib import Path

CTL_DAYS = 42
ATL_DAYS = 7

DATE_RE = re.compile(r"^### (\d{4}-\d{2}-\d{2}) ")
TSS_RE = re.compile(r"^\*\*TSS\*\*:\s*([\d.]+)")

DEFAULT_LOGS_DIR = "training-log"
DEFAULT_OUTPUT = "health-log/training-load.md"


def collect_daily_tss(logs_dir: str) -> dict[date, float]:
    """Sum TSS per calendar day across every training-log/week-*.md file."""
    daily: dict[date, float] = {}
    for path in glob.glob(str(Path(logs_dir) / "week-*.md")):
        current_date = None
        for line in Path(path).read_text().splitlines():
            m = DATE_RE.match(line)
            if m:
                current_date = date.fromisoformat(m.group(1))
                continue
            m = TSS_RE.match(line)
            if m and current_date is not None:
                daily[current_date] = daily.get(current_date, 0.0) + float(m.group(1))
    return daily


def compute_load_series(daily_tss: dict[date, float], end: date) -> list[dict]:
    """Day-by-day CTL/ATL/TSB from the first logged day through `end`, zero-filling gaps."""
    if not daily_tss:
        return []
    start = min(daily_tss)

    rows = []
    ctl = 0.0
    atl = 0.0
    day = start
    while day <= end:
        tss_today = daily_tss.get(day, 0.0)
        tsb_today = ctl - atl  # form going into today, before today's TSS
        ctl = ctl + (tss_today - ctl) / CTL_DAYS
        atl = atl + (tss_today - atl) / ATL_DAYS
        rows.append({"date": day, "tss": tss_today, "ctl": ctl, "atl": atl, "tsb": tsb_today})
        day += timedelta(days=1)
    return rows


def interpret_tsb(tsb: float) -> str:
    """Standard TrainingPeaks/Coggan TSB reference zones."""
    if tsb > 25:
        return "molto fresco (rischio di perdere forma se prolungato)"
    if tsb > 5:
        return "fresco, pronto per gareggiare"
    if tsb > -10:
        return "zona grigia (ne fresco ne in costruzione produttiva)"
    if tsb > -30:
        return "zona ottimale di allenamento (carico produttivo)"
    return "zona ad alto rischio (sovraccarico)"


def interpret_acwr(acwr: float | None) -> str:
    """Acute:Chronic Workload Ratio (Gabbett) - injury-risk read on ATL relative to CTL."""
    if acwr is None:
        return "n/d"
    if acwr < 0.8:
        return "sotto-allenato"
    if acwr <= 1.3:
        return "fascia a basso rischio"
    if acwr <= 1.5:
        return "fascia di attenzione"
    return "rischio infortunio elevato"


def build_markdown(rows: list[dict]) -> str:
    days_logged = len(rows)
    ramp_pct = min(100, round(100 * days_logged / CTL_DAYS))

    lines = [
        "# Training Load (CTL / ATL / TSB)",
        "",
        "Stile TrainingPeaks, calcolato dal TSS giornaliero (somma dei TSS per attivita in training-log/week-*.md, "
        "a sua volta da NGP/IF in garmin_sync.py). Giorni senza attivita contano 0, non vengono saltati.",
        "",
        f"- **CTL** (Chronic Training Load, \"fitness\"): media mobile esponenziale del TSS su {CTL_DAYS} giorni.",
        f"- **ATL** (Acute Training Load, \"fatigue\"): media mobile esponenziale del TSS su {ATL_DAYS} giorni.",
        "- **TSB** (Training Stress Balance, \"form\") = CTL - ATL del giorno precedente, cioe la freschezza con cui affronti la giornata, prima del suo stesso carico.",
        "- **ACWR** (Acute:Chronic Workload Ratio) = ATL/CTL - il modo corretto di leggere il rischio dell'ATL: un ATL assoluto non dice nulla senza sapere quanto CTL c'e sotto a sostenerlo.",
        "",
        "Fasce TSB (convenzione TrainingPeaks/Coggan): >+25 molto fresco, +5/+25 fresco, -10/+5 zona grigia, "
        "-30/-10 zona ottimale di allenamento, <-30 alto rischio.",
        "Fasce ACWR (Gabbett): <0.8 sotto-allenato, 0.8-1.3 basso rischio, 1.3-1.5 attenzione, >1.5 rischio infortunio elevato.",
        "",
    ]

    if not rows:
        lines.append("Nessun dato TSS trovato in training-log/.")
        return "\n".join(lines)

    last = rows[-1]
    acwr = last["atl"] / last["ctl"] if last["ctl"] else None
    lines.append(
        f"**Stato attuale ({last['date'].isoformat()})**: CTL {last['ctl']:.1f} | ATL {last['atl']:.1f} | "
        f"TSB {last['tsb']:+.1f} ({interpret_tsb(last['tsb'])}) | ACWR {acwr:.2f} ({interpret_acwr(acwr)})" if acwr is not None else
        f"**Stato attuale ({last['date'].isoformat()})**: CTL {last['ctl']:.1f} | ATL {last['atl']:.1f} | "
        f"TSB {last['tsb']:+.1f} ({interpret_tsb(last['tsb'])})"
    )
    if ramp_pct < 100:
        lines.append(
            f"- Solo {days_logged} giorni di storico su {CTL_DAYS} necessari perche il CTL converga del tutto "
            f"(~{ramp_pct}% del transitorio) - i numeri (TSB e soprattutto ACWR, che dipende direttamente dal CTL) "
            "sono ancora in fase di costruzione: un CTL artificialmente basso gonfia l'ACWR rispetto a quello che "
            "sara una volta assestato. Non prenderli come plateau stabile."
        )
    lines.append("")

    lines.append("| Data | TSS | CTL | ATL | TSB | ACWR |")
    lines.append("| ---------- | ---: | ---: | ---: | ---: | ---: |")
    for row in rows:
        row_acwr = row["atl"] / row["ctl"] if row["ctl"] else None
        acwr_str = f"{row_acwr:.2f}" if row_acwr is not None else "n/d"
        lines.append(
            f"| {row['date'].isoformat()} | {row['tss']:.0f} | {row['ctl']:.1f} | {row['atl']:.1f} | {row['tsb']:+.1f} | {acwr_str} |"
        )
    lines.append("")

    return "\n".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(description="Calculate CTL/ATL/TSB from logged TSS values")
    parser.add_argument("--logs-dir", default=DEFAULT_LOGS_DIR, help=f"Directory with week-*.md files (default: {DEFAULT_LOGS_DIR})")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help=f"Output markdown file (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--end-date", type=str, help="YYYY-MM-DD, last day to compute through (default: today)")
    return parser.parse_args()


def main():
    args = parse_args()
    end = date.fromisoformat(args.end_date) if args.end_date else date.today()

    daily_tss = collect_daily_tss(args.logs_dir)
    rows = compute_load_series(daily_tss, end)
    markdown = build_markdown(rows)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown)

    if rows:
        last = rows[-1]
        acwr = last["atl"] / last["ctl"] if last["ctl"] else None
        acwr_part = f" | ACWR {acwr:.2f} ({interpret_acwr(acwr)})" if acwr is not None else ""
        print(f"CTL {last['ctl']:.1f} | ATL {last['atl']:.1f} | TSB {last['tsb']:+.1f} ({interpret_tsb(last['tsb'])}){acwr_part}")
    print(f"Wrote {output_path} ({len(rows)} days)")


if __name__ == "__main__":
    main()
