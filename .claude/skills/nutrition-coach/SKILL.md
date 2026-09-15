---
name: nutrition-coach
description: Guided nutrition assessment, weight-loss planning, maintenance planning, and daily meal coaching based on the athlete's profile and food log.
---

# Nutrition Coach

Delegate conversational nutrition coaching to `.claude/agents/nutrition-coach/AGENTS.md` and use this skill as its operating context.

Use `.claude/skills/nutrition-coach/scripts/nutrition_assessment.py` for the first interview and calorie/macro calculations.

## First assessment

Run:

```bash
python3 .claude/skills/nutrition-coach/scripts/nutrition_assessment.py
```

The script asks for sex, age, height, current and target weight, activity level, and whether the athlete wants a short, medium, or long diet period. It calculates BMR with Mifflin-St Jeor, estimates TDEE, derives the daily deficit from the selected duration, and calculates protein, fat, and carbohydrate targets. It also writes maintenance targets at the goal weight.

Default periods are 8, 16, and 24 weeks. They are planning choices, not medical prescriptions. The script caps the calculated deficit and warns when the resulting intake is unusually low; a clinician or registered dietitian should review a plan when there is a medical condition, eating-disorder history, medication, pregnancy, or persistent symptoms.

## Data sources

- Garmin sync writes daily weight to `health-log/daily-health.md` when Garmin body-composition data is available.
- Waist circumference is manual and belongs in `nutrition-log/measurements.md`.
- The saved assessment is `nutrition-log/nutrition-profile.json` and the readable result is `nutrition-log/initial-assessment.md`.

## Daily coaching

When the athlete reports food, record it in `nutrition-log/daily-food.md` and use the profile, current Garmin weight trend, training load, hunger, sleep, and available cafeteria/home-dinner options. Give practical substitutions rather than rigid meal prescriptions. Do not infer calories or macros when portions are unknown; ask for one missing quantity at a time.

Keep `nutrition-log/daily-food.md` compact, not a narrative log: one heading per day carrying the totals and score (`## YYYY-MM-DD — X kcal (target Y) | P.. C.. G.. | score N/100`), then one line per meal (items, assumed portion, estimated kcal), and a short notes line for quality flags (fruit/veg, Garmin, alcohol). The assumption reasoning and uncertainty ranges belong in the conversation while estimating, not in the file — write only the resulting estimate. When the athlete asks for a weekly or monthly review, read `nutrition-log/nutrition-summary.md` (daily rows plus weekly/month-to-date averages, with days-logged coverage) instead of re-reading the raw daily entries.

The athlete usually does not provide precise weights or measurements. Do not block the assessment waiting for exact portions: estimate calories and macros from standard portions, state the assumptions, and give a plausible range. Use the estimate to assess alignment with the daily targets and the protein/carbohydrate/fat distribution. Ask for a precise quantity only when it would materially improve the estimate, and continue to provide the best current estimate.