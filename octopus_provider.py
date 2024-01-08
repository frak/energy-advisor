from datetime import datetime
from typing import List, Dict

from octopus_client import OctopusClient


class OctopusProvider:
    def __init__(self, client: OctopusClient):
        self.client = client

    def _get_gsp(self, mpan: str) -> str:
        return self.client.electricity_meter_point(mpan)["gsp"][1:]

    def _get_daily_prices(self, gsp: str, start_at: datetime):
        res = self.client.agile_tariff_unit_rates(gsp, period_from=start_at)["results"]
        return sorted(res, key=lambda item: item["valid_from"])

    @staticmethod
    def _calculate_windows(prices: List[dict]) -> dict:
        single_price, single_start, group_price, group_start = 99, None, 99, None
        for index, price in enumerate(prices):
            if price["value_inc_vat"] < single_price:
                single_price = price["value_inc_vat"]
                single_start = datetime.strptime(
                    price["valid_from"], "%Y-%m-%dT%H:%M:%SZ"
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
                        price["valid_from"], "%Y-%m-%dT%H:%M:%SZ"
                    )
            except IndexError:
                pass
        return {
            "cheapest_slot": single_start,
            "slot_price": single_price,
            "cheapest_group": group_start,
        }

    def get_price_windows(self, mpan: str, start: datetime) -> Dict[str, str]:
        gsp = self._get_gsp(mpan)
        day_prices = self._get_daily_prices(gsp, start)
        if not day_prices:
            raise RuntimeError(
                "No prices returned, are you running this script before 4pm?"
            )
        out = self._calculate_windows(day_prices)
        out["run_for"] = start
        return out
