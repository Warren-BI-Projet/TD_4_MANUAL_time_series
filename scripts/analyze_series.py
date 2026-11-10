"""Clean, smooth and project the daily CO2 series."""

import csv
import json
import os
from datetime import date, datetime, timedelta, timezone

WINDOW = 7
ALPHA = 0.3
PROJECT_STEPS = 7
SOURCE = "data/series.csv"
OUTPUT = "docs/data/series_analysis.json"


def load_series(path=SOURCE):
    with open(path, newline="", encoding="utf-8") as stream:
        return [
            {"date": row["date"], "value": float(row["co2_ppm"]),
             "n_hours_observed": int(row["n_hours_observed"])}
            for row in csv.DictReader(stream) if row["co2_ppm"]
        ]


def clean_series(rows):
    if not rows:
        raise ValueError("No daily observations available")
    by_date = {row["date"]: row for row in rows}
    start = min(date.fromisoformat(day) for day in by_date)
    end = max(date.fromisoformat(day) for day in by_date)
    cleaned = []
    for day_index in range((end - start).days + 1):
        day = (start + timedelta(days=day_index)).isoformat()
        source = by_date.get(day)
        cleaned.append({
            "day": day_index,
            "date": day,
            "value": source["value"] if source else None,
            "n_hours_observed": source["n_hours_observed"] if source else 0,
        })
    gaps = []
    for row in cleaned:
        if row["value"] is None:
            if gaps and gaps[-1]["end_day"] == row["day"] - 1:
                gaps[-1]["end_day"] = row["day"]
                gaps[-1]["end_date"] = row["date"]
            else:
                gaps.append({"start_day": row["day"], "end_day": row["day"],
                             "start_date": row["date"], "end_date": row["date"]})
    return cleaned, gaps, start


def rolling_mean(values, window=WINDOW):
    result = []
    for i in range(len(values)):
        subset = [value for value in values[max(0, i - window + 1):i + 1]
                  if value is not None]
        result.append(round(sum(subset) / len(subset), 2) if subset else None)
    return result


def exponential_smoothing(values, alpha=ALPHA):
    result = []
    state = None
    for value in values:
        if value is not None:
            state = value if state is None else round(alpha * value + (1 - alpha) * state, 2)
        result.append(state)
    return result


def linear_trend_projection(rows, start, steps=PROJECT_STEPS):
    observed = [row for row in rows if row["value"] is not None]
    days = [row["day"] for row in observed]
    values = [row["value"] for row in observed]
    mean_day = sum(days) / len(days)
    mean_value = sum(values) / len(values)
    denominator = sum((day - mean_day) ** 2 for day in days)
    slope = (sum((day - mean_day) * (value - mean_value)
                 for day, value in zip(days, values)) / denominator) if denominator else 0.0
    intercept = mean_value - slope * mean_day
    projection = []
    for step in range(1, steps + 1):
        day = days[-1] + step
        projection.append({"day": day, "date": (start + timedelta(days=day)).isoformat(),
                           "value": round(intercept + slope * day, 2)})
    return projection, slope


def main():
    cleaned, gaps, start = clean_series(load_series())
    values = [row["value"] for row in cleaned]
    rolling = rolling_mean(values)
    smoothed = exponential_smoothing(values)
    projection, slope = linear_trend_projection(cleaned, start)
    observed = [row for row in cleaned if row["value"] is not None]
    incomplete = [row for row in observed if row["n_hours_observed"] < 24]
    note = (
        f"Projection linéaire sur {PROJECT_STEPS} jours à partir de {len(observed)} jours observés ; "
        f"{len(gaps)} période(s) manquante(s), {len(incomplete)} jour(s) incomplet(s). "
        "Le CO₂ suit un cycle saisonnier : la pente de cette fenêtre de 90 jours "
        "ne doit pas être prolongée au-delà de quelques jours ni à travers un changement de saison."
    )
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "location": "Le Mans (48.0061, 0.1996)", "source": "Open-Meteo Air Quality (CAMS)",
        "unit": "ppm", "raw": cleaned, "gaps": gaps,
        "rolling_mean": [{"day": row["day"], "value": value} for row, value in zip(cleaned, rolling)],
        "exp_smoothed": [{"day": row["day"], "value": value} for row, value in zip(cleaned, smoothed)],
        "projection": projection, "trend_slope_per_day": round(slope, 4),
        "honest_note": note,
    }
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as stream:
        json.dump(output, stream, ensure_ascii=False, indent=2)
    print(f"Observed {len(observed)} days; {len(gaps)} gap(s); {len(incomplete)} incomplete day(s)")
    print(f"Last five raw: {[row['value'] for row in observed[-5:]]}")
    print(f"Last five rolling: {[value for value in rolling if value is not None][-5:]}")
    print(f"Last five exponential: {[value for value in smoothed if value is not None][-5:]}")
    print(f"Slope: {slope:+.4f} ppm/day; projection: {[row['value'] for row in projection]}")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
