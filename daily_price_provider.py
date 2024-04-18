from datetime import datetime
from typing import List, Dict

from pytz import timezone

from octopus_client import OctopusClient


class DailyPriceProvider:
    def __init__(self, client: OctopusClient):
        self.client = client

    @staticmethod
    def _calculate_windows(prices: List[Dict]) -> dict:
        single_price, single_start, group_price, group_start = 99, None, 99, None
        for index, price in enumerate(prices):
            if price["value_inc_vat"] < single_price:
                single_price = price["value_inc_vat"]
                single_start = datetime.strptime(
                    price["valid_from"], "%Y-%m-%dT%H:%M:%S%z"
                )
            try:
                this_group_price = (
                    price["value_inc_vat"]
                    + prices[index + 1]["value_inc_vat"]
                    + prices[index + 2]["value_inc_vat"]
                )
                if this_group_price < group_price:
                    group_price = this_group_price
                    group_start = datetime.strptime(
                        price["valid_from"], "%Y-%m-%dT%H:%M:%S%z"
                    )
            except IndexError:
                pass
        return {
            "cheapest_slot": single_start.astimezone(timezone("Europe/London")),
            "slot_price": single_price,
            "cheapest_group": group_start.astimezone(timezone("Europe/London")),
        }

    def get_price_windows(self, start: datetime) -> Dict[str, str]:
        day_prices = self.client.get_daily_prices(start)
        out = self._calculate_windows(day_prices)
        out["run_for"] = start.astimezone(timezone("Europe/London"))
        return out
