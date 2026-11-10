"""Stage 6: compare the Le Mans trend with a second real location."""

from analyze_series import clean_series, linear_trend_projection
from fetch_series import aggregate_to_daily, fetch_hourly_co2


def trend_for(lat, lon):
    times, values = fetch_hourly_co2(lat, lon)
    daily = aggregate_to_daily(times, values)
    observations = [
        {"date": row["date"], "value": row["co2_ppm"],
         "n_hours_observed": row["n_hours_observed"]}
        for row in daily if row["co2_ppm"] != ""
    ]
    cleaned, gaps, start = clean_series(observations)
    _, slope = linear_trend_projection(cleaned, start)
    return len(observations), len(gaps), slope


if __name__ == "__main__":
    for location, lat, lon in [("Le Mans", 48.0061, 0.1996),
                               ("Madrid", 40.4168, -3.7038)]:
        count, gaps, slope = trend_for(lat, lon)
        print(f"{location}: {count} days, {gaps} gap(s), {slope:+.4f} ppm/day")
