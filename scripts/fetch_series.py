"""Collect daily atmospheric CO2 for Le Mans from Open-Meteo."""

import csv
import os
import time
from collections import defaultdict
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen
import json

LAT, LON = 48.0061, 0.1996
PAST_DAYS = 90
URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
OUTPUT = "data/series.csv"


def fetch_hourly_co2(lat=LAT, lon=LON, retries=4, backoff=5):
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "carbon_dioxide",
        "past_days": PAST_DAYS,
        "forecast_days": 0,
        "timezone": "auto",
    }
    for attempt in range(1, retries + 1):
        try:
            with urlopen(f"{URL}?{urlencode(params)}", timeout=30) as response:
                payload = json.load(response)
            times = payload["hourly"]["time"]
            values = payload["hourly"]["carbon_dioxide"]
            if not times or len(times) != len(values):
                raise ValueError("Invalid hourly CO2 response")
            return times, values
        except (HTTPError, URLError, TimeoutError, KeyError, ValueError) as error:
            print(f"Fetch attempt {attempt}/{retries} failed: {error}")
            if attempt == retries:
                raise RuntimeError("Open-Meteo data unavailable") from error
            time.sleep(backoff * attempt)


def aggregate_to_daily(times, values):
    by_day = defaultdict(list)
    for timestamp, value in zip(times, values):
        by_day[timestamp[:10]].append(value)
    rows = []
    for day, hours in sorted(by_day.items()):
        observed = [value for value in hours if value is not None]
        rows.append({
            "date": day,
            "co2_ppm": round(sum(observed) / len(observed), 1) if observed else "",
            "n_hours_observed": len(observed),
        })
    return rows


def main():
    times, values = fetch_hourly_co2()
    rows = aggregate_to_daily(times, values)
    print(f"Le Mans: {len(times)} hourly values, {len(rows)} daily rows")
    for row in rows:
        if row["n_hours_observed"] < 24:
            print(f"Incomplete day: {row['date']} ({row['n_hours_observed']}/24 hours)")
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["date", "co2_ppm", "n_hours_observed"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
