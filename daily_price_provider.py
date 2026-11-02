from datetime import datetime
from typing import List, Dict

from pytz import timezone

from octopus_client import OctopusClient

LONDON = timezone("Europe/London")
GROUP_SLOTS = 3


class DailyPriceProvider:
    def __init__(self, client: OctopusClient):
        self.client = client

    @staticmethod
    def _slot_start(price: Dict) -> datetime:
        return datetime.strptime(price["valid_from"], "%Y-%m-%dT%H:%M:%S%z").astimezone(LONDON)

    @classmethod
    def _calculate_windows(cls, prices: List[Dict]) -> dict:
        if len(prices) < GROUP_SLOTS:
            raise ValueError(
                f"Need at least {GROUP_SLOTS} price slots to find a charging window, got {len(prices)}"
            )

        cheapest_slot = min(prices, key=lambda price: price["value_inc_vat"])

        # Taking min() of the real sums rather than beating a fixed starting price: a sentinel sized
        # for one slot (99) is smaller than any 3-slot sum once prices average over 33p/kWh, so the
        # group search silently found nothing and left the start time None.
        groups = (
            prices[index:index + GROUP_SLOTS]
            for index in range(len(prices) - GROUP_SLOTS + 1)
        )
        cheapest_group = min(
            groups, key=lambda group: sum(slot["value_inc_vat"] for slot in group)
        )

        return {
            "cheapest_slot": cls._slot_start(cheapest_slot),
            "slot_price": cheapest_slot["value_inc_vat"],
            "cheapest_group": cls._slot_start(cheapest_group[0]),
        }

    def get_price_windows(self, start: datetime) -> Dict[str, str]:
        day_prices = self.client.get_daily_prices(start)
        out = self._calculate_windows(day_prices)
        out["run_for"] = start.astimezone(LONDON)
        return out
