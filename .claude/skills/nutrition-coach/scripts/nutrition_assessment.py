#!/usr/bin/env python3
"""Run a guided nutrition assessment and save calorie/macro targets."""

import json
import argparse
from datetime import date
from pathlib import Path


PERIODS = {"breve": (8, "8 settimane"), "medio": (16, "16 settimane"), "lungo": (24, "24 settimane")}
ACTIVITY_LEVELS = {
    "1": (1.2, "sedentario, poco movimento oltre agli allenamenti"),
    "2": (1.375, "leggermente attivo, movimento leggero e 1-3 allenamenti"),
    "3": (1.55, "moderatamente attivo, 3-5 allenamenti o lavoro in piedi"),
    "4": (1.725, "molto attivo, allenamento frequente o lavoro fisico"),
    "5": (1.9, "estremamente attivo, lavoro fisico e allenamento intenso"),
}


def ask(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Inserisci un valore.")


def ask_float(prompt: str, minimum: float | None = None) -> float:
    while True:
        try:
            value = float(ask(prompt).replace(",", "."))
            if minimum is not None and value < minimum:
                raise ValueError
            return value
        except ValueError:
            print("Numero non valido.")


def ask_choice(prompt: str, choices: set[str]) -> str:
    while True:
        value = ask(prompt).lower()
        if value in choices:
            return value
        print(f"Scegli una delle opzioni: {', '.join(sorted(choices))}")


def round_target(value: float) -> int:
    return int(round(value / 10) * 10)


def calculate(sex: str, age: int, height: float, weight: float, goal_weight: float, activity_factor: float, weeks: int) -> dict:
    sex_constant = 5 if sex == "uomo" else -161
    bmr = 10 * weight + 6.25 * height - 5 * age + sex_constant
    maintenance_now = bmr * activity_factor
    goal_bmr = 10 * goal_weight + 6.25 * height - 5 * age + sex_constant
    maintenance_goal = goal_bmr * activity_factor
    loss_kg = max(0.0, weight - goal_weight)
    daily_deficit = min(750.0, loss_kg * 7700 / (weeks * 7))
    floor = 1500.0 if sex == "uomo" else 1200.0
    calories = max(floor, maintenance_now - daily_deficit)
    protein = 1.8 * goal_weight if loss_kg / weight > 0.1 else 1.6 * goal_weight
    fat = 0.8 * goal_weight
    carbs = max(0.0, (calories - protein * 4 - fat * 9) / 4)
    maintenance_protein = 1.6 * goal_weight
    maintenance_fat = 0.8 * goal_weight
    maintenance_carbs = max(0.0, (maintenance_goal - maintenance_protein * 4 - maintenance_fat * 9) / 4)
    return {
        "bmr_now_kcal": round_target(bmr), "tdee_now_kcal": round_target(maintenance_now),
        "diet_calories_kcal": round_target(calories), "daily_deficit_kcal": round_target(maintenance_now - calories),
        "protein_g": round(protein), "fat_g": round(fat), "carbs_g": round(carbs),
        "maintenance_at_goal": {"bmr_kcal": round_target(goal_bmr), "tdee_kcal": round_target(maintenance_goal),
            "calories_kcal": round_target(maintenance_goal), "protein_g": round(maintenance_protein),
            "fat_g": round(maintenance_fat), "carbs_g": round(maintenance_carbs)},
    }


def render(profile: dict) -> str:
    result = profile["targets"]
    maintenance = result["maintenance_at_goal"]
    return f"""# Assessment nutrizionale iniziale

Data: {profile['assessment_date']}

## Profilo

- Sesso: {profile['sex']}
- Età: {profile['age']} anni
- Altezza: {profile['height_cm']:.0f} cm
- Peso attuale: {profile['weight_kg']:.1f} kg
- Peso obiettivo: {profile['goal_weight_kg']:.1f} kg
- Circonferenza vita: da inserire manualmente in `nutrition-log/measurements.md`
- Attività: {profile['activity_description']}
- Periodo dimagrimento: {profile['diet_period_label']}

## Dimagrimento

- Metabolismo basale stimato: **{result['bmr_now_kcal']} kcal/giorno**
- Fabbisogno di mantenimento stimato ora: **{result['tdee_now_kcal']} kcal/giorno**
- Target iniziale: **{result['diet_calories_kcal']} kcal/giorno**
- Deficit medio calcolato: **{result['daily_deficit_kcal']} kcal/giorno**
- Macro: **{result['protein_g']} g proteine**, **{result['fat_g']} g grassi**, **{result['carbs_g']} g carboidrati**

## Mantenimento al peso obiettivo

- BMR stimato: **{maintenance['bmr_kcal']} kcal/giorno**
- TDEE stimato: **{maintenance['tdee_kcal']} kcal/giorno**
- Target iniziale: **{maintenance['calories_kcal']} kcal/giorno**
- Macro: **{maintenance['protein_g']} g proteine**, **{maintenance['fat_g']} g grassi**, **{maintenance['carbs_g']} g carboidrati**

## Note

Sono stime iniziali: dopo 2-3 settimane si ricalibrano usando media del peso, fame, sonno, allenamenti e prestazioni. Il peso Garmin è un dato da dispositivo consumer e può oscillare per acqua, glicogeno e contenuto intestinale. Non usare il singolo giorno per modificare le calorie.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print("Assessment nutrizionale iniziale")
    print("Le calorie sono stime pratiche, non prescrizioni mediche.\n")
    sex = ask_choice("Sesso biologico (uomo/donna): ", {"uomo", "donna"})
    age = int(ask_float("Età in anni: ", 1))
    height = ask_float("Altezza in cm: ", 100)
    weight = ask_float("Peso attuale in kg: ", 30)
    goal_weight = ask_float("Peso obiettivo in kg: ", 30)
    activity = ask_choice("Livello attività (1 sedentario, 2 leggero, 3 moderato, 4 alto, 5 estremo): ", set(ACTIVITY_LEVELS))
    period = ask_choice("Periodo dieta (breve/medio/lungo): ", set(PERIODS))
    weeks, period_label = PERIODS[period]
    factor, activity_description = ACTIVITY_LEVELS[activity]
    profile = {"assessment_date": date.today().isoformat(), "sex": sex, "age": age, "height_cm": height,
        "weight_kg": weight, "goal_weight_kg": goal_weight, "activity_factor": factor,
        "activity_description": activity_description, "diet_period": period, "diet_period_label": period_label,
        "diet_weeks": weeks, "targets": calculate(sex, age, height, weight, goal_weight, factor, weeks)}
    output_dir = Path("nutrition-log")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "nutrition-profile.json").write_text(json.dumps(profile, indent=2) + "\n")
    (output_dir / "initial-assessment.md").write_text(render(profile))
    measurements = output_dir / "measurements.md"
    if not measurements.exists():
        measurements.write_text("# Misure corporee\n\nInserimento manuale della circonferenza vita.\n\n| Data | Circonferenza vita (cm) | Note |\n|---|---:|---|\n")
    daily_food = output_dir / "daily-food.md"
    if not daily_food.exists():
        daily_food.write_text("# Diario alimentare\n\nInserire qui pasti, porzioni approssimative, fame, energia e note.\n")
    print("\n" + render(profile))
    print(f"Salvati: {output_dir / 'nutrition-profile.json'} e {output_dir / 'initial-assessment.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())