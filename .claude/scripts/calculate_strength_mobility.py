#!/usr/bin/env python3
"""
Strength (FS) and mobility/control (MCS) indices from the monthly test battery
in health-log/strength-mobility.md.

Each test scores (weaker side / reference) x 100, capped at 100: 100 means
"adequate for a runner", and only the weaker side counts, so the index moves
only when the weak side improves. Yes/no checks score the share of passes.

FS  = mean of single-leg calf raise, side plank, single-leg glute bridge
MCS = mean of knee-to-wall, eyes-closed single-leg balance, single-leg half
      squat (pelvis level + knee over foot, per side) and modified Thomas test

The results table is the input; a "## Indici" section (ISO dates, read by
monthly_profile.py) is rewritten at the end of the file.

Usage:
    python3 .claude/scripts/calculate_strength_mobility.py
"""

import argparse
import re
from datetime import datetime
from pathlib import Path

DEFAULT_FILE = "health-log/strength-mobility.md"
INDEX_HEADING = "## Indici"

# label, results-table columns (dx, sx), reference value
STRENGTH_TESTS = [
    ("Calf raise", ("Calf raise dx", "Calf raise sx"), 25),
    ("Side plank", ("Side plank dx", "Side plank sx"), 60),
    ("Bridge 1 gamba", ("Bridge 1 gamba dx", "Bridge 1 gamba sx"), 20),
]
MOBILITY_TESTS = [
    ("Ginocchio-muro", ("Ginocchio-muro dx", "Ginocchio-muro sx"), 10),
    ("Equilibrio", ("Equilibrio dx", "Equilibrio sx"), 30),
]


def first_number(text: str) -> float | None:
    m = re.search(r"\d+(?:\.\d+)?", text)
    return float(m.group(0)) if m else None


def results_rows(text: str) -> list[dict]:
    """Rows of the results table (the one whose first column is 'Data' with dd/mm/yyyy dates)."""
    rows, headers = [], None
    for line in text.splitlines():
        if not line.startswith("|"):
            headers = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells[0] == "Data":
            headers = cells
        elif headers and re.match(r"\d{2}/\d{2}/\d{4}$", cells[0]):
            rows.append(dict(zip(headers, cells)))
    return rows


def side_score(row: dict, columns: tuple[str, str], reference: float) -> tuple[float, float] | None:
    values = [first_number(row.get(c, "")) for c in columns]
    if any(v is None for v in values):
        return None
    weaker = min(values)
    return weaker, min(weaker / reference, 1.0) * 100


def pass_share(cell: str, passing: str) -> float | None:
    """'dx no / sx si' -> share of sides with the passing answer."""
    answers = [part.split()[-1].lower() for part in cell.split("/") if part.strip()]
    if not answers:
        return None
    return sum(a == passing for a in answers) / len(answers) * 100


def score_row(row: dict) -> dict:
    strength = {label: side_score(row, cols, ref) for label, cols, ref in STRENGTH_TESTS}
    mobility = {label: side_score(row, cols, ref) for label, cols, ref in MOBILITY_TESTS}
    pelvis = pass_share(row.get("Bacino scende (dx/sx)", ""), "no")
    knee = pass_share(row.get("Ginocchio dentro (dx/sx)", ""), "no")
    squat = (pelvis + knee) / 2 if pelvis is not None and knee is not None else None
    thomas = pass_share(row.get("Thomas dx/sx", ""), "ok")

    fs_parts = [s[1] for s in strength.values() if s]
    mcs_parts = [s[1] for s in mobility.values() if s] + [v for v in (squat, thomas) if v is not None]
    return {
        "date": datetime.strptime(row["Data"], "%d/%m/%Y").date(),
        "strength": strength,
        "mobility": mobility,
        "squat": squat,
        "thomas": thomas,
        "fs": sum(fs_parts) / len(fs_parts) if len(fs_parts) == len(STRENGTH_TESTS) else None,
        "mcs": sum(mcs_parts) / len(mcs_parts) if len(mcs_parts) == len(MOBILITY_TESTS) + 2 else None,
    }


def fmt(value: float | None) -> str:
    return "n/d" if value is None else f"{value:.0f}"


def build_section(scores: list[dict]) -> str:
    ref = lambda tests: ", ".join(f"{label} {r:g}" for label, _cols, r in tests)  # noqa: E731
    lines = [
        INDEX_HEADING,
        "",
        "Generato da `.claude/scripts/calculate_strength_mobility.py` dalla tabella dei risultati: rilanciarlo dopo ogni test. "
        "Ogni test vale (lato piu debole / riferimento) x 100, con tetto a 100: 100 = adeguato per un runner. "
        "Conta solo il lato piu debole, quindi l'indice sale solo se migliora quello. Nel profilo mensile e nel radar entrano come indice 100 = primo test.",
        "",
        f"- **FS (Forza)**: media di calf raise, side plank e bridge su una gamba. Riferimenti: {ref(STRENGTH_TESTS)}.",
        f"- **MCS (Mobilita e controllo)**: media di ginocchio-muro, equilibrio a occhi chiusi, mezzo squat su una gamba "
        f"(bacino in bolla + ginocchio sopra il piede, per lato) e test di Thomas. Riferimenti: {ref(MOBILITY_TESTS)}.",
        "",
        "| Data | FS | MCS | Calf raise | Side plank | Bridge | Ginocchio-muro | Equilibrio | Squat 1 gamba | Thomas |",
        "| ---------- | --: | --: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for s in scores:
        cells = [s["date"].isoformat(), fmt(s["fs"]), fmt(s["mcs"])]
        for group in (s["strength"], s["mobility"]):
            for value in group.values():
                cells.append("n/d" if value is None else f"{value[0]:g} -> {value[1]:.0f}")
        cells += [fmt(s["squat"]), fmt(s["thomas"])]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    return "\n".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(description="Strength and mobility indices from the monthly test battery")
    parser.add_argument("--file", default=DEFAULT_FILE, help=f"Test results markdown (default: {DEFAULT_FILE})")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.file)
    text = path.read_text()
    scores = [score_row(row) for row in results_rows(text)]
    if not scores:
        print("No test results found.")
        return 0

    body = text.split("\n" + INDEX_HEADING + "\n")[0].rstrip("\n")
    path.write_text(body + "\n\n" + build_section(scores))
    for s in scores:
        print(f"{s['date'].isoformat()}: FS {fmt(s['fs'])} | MCS {fmt(s['mcs'])}")
    print(f"Logged indices to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
