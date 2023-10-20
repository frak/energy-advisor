import json
import os
from datetime import datetime
from typing import Dict, List

import requests

# Solar panel information
LAT = os.getenv("LAT")
LNG = os.getenv("LNG")
DEC = os.getenv("DEC")
AZ = os.getenv("AZ")
KWP = os.getenv("KWP")

REQUEST_URL = "https://api.forecast.solar/estimate/watthours/day/{lat}/{lng}/{dec}/{az}/{kwp}"
DATA_FILE = f"{os.path.dirname(os.path.realpath(__file__))}/data/forecasts.json"


def store_forecasts(lat: str, lng: str, declination: str, azimuth: str, kwp: str) -> None:
    url = REQUEST_URL.format(lat=lat, lng=lng, dec=declination, az=azimuth, kwp=kwp)
    result = get_data(url)["result"]
    forecasts = get_forecasts()
    add_new_values(forecasts, result)
    prune_old_values(forecasts)
    write_forecasts(forecasts)


def get_forecasts() -> Dict[str, List[int]]:
    if os.path.isfile(DATA_FILE):
        with open(DATA_FILE, "rb") as file:
            forecasts = json.loads(file.read())
    else:
        forecasts = {}
    return forecasts


def add_new_values(forecasts: Dict[str, List[int]], result: Dict[str, int]):
    for date, value in result.items():
        if date in forecasts:
            forecasts[date].append(value)
        else:
            forecasts[date] = [value]


def prune_old_values(forecasts: Dict[str, List[int]]):
    now = datetime.now()
    for date in list(forecasts.keys()):
        forecast_date = datetime.strptime(date, "%Y-%m-%d")
        if forecast_date <= now:
            del forecasts[date]


def write_forecasts(forecasts: Dict[str, List[int]]):
    with open(DATA_FILE, "wb") as file:
        file.write(json.dumps(forecasts, indent=2).encode('utf8'))


def get_data(url) -> Dict:
    return requests.get(url).json()


if __name__ == "__main__":
    if LAT is None or LNG is None or DEC is None or AZ is None or KWP is None:
        print(f"Required env vars are missing, please check: {LAT=}, {LNG=}, {DEC=}, {AZ=}, {KWP=}")
        exit(1)
    store_forecasts(LAT, LNG, DEC, AZ, KWP)
