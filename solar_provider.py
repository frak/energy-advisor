import json
import os
from statistics import mean
from typing import Dict, Union

from collector import DATA_FILE


class SolarProvider:
    forecasts: Dict

    def __init__(self):
        if not os.path.isfile(DATA_FILE):
            self.forecasts = {}
        else:
            with open(DATA_FILE, "rb") as file:
                self.forecasts = json.loads(file.read())

    def get_mean_and_range_for_date(self, date: str) -> Dict[str, Union[int, float]]:
        if date not in self.forecasts:
            return {}
        values = self.forecasts[date]
        return {
            "mean": mean(values),
            "min": min(values),
            "max": max(values),
            "count": len(values),
        }

