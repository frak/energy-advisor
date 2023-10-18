import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict

from mastodon import Mastodon

from octopus_client import OctopusClient

# Octopus
OCTOPUS_TOKEN = os.getenv("OCTOPUS_TOKEN")
MPAN = "1013086411200"
octo_client = OctopusClient(OCTOPUS_TOKEN)

# Mastodon
MASTO_TOKEN = os.getenv("MASTO_TOKEN")
BOT_HOME = os.getenv("BOT_HOME", "https://botsin.space")
masto_client = Mastodon(access_token=MASTO_TOKEN, api_base_url=BOT_HOME)


def get_gsp() -> str:
    return octo_client.electricity_meter_point(MPAN)["gsp"][1:]


def get_daily_prices(gsp: str, start_at: datetime, end_at: datetime):
    res = octo_client.agile_tariff_unit_rates(gsp, period_from=start_at, period_to=end_at)["results"]
    out = sorted(res, key=lambda item: item["valid_from"])
    return out


def get_cheapest_windows(prices: List[dict]) -> dict:
    single_price = 99999
    single_start = None
    group_price = 99999
    group_start = None
    for index, price in enumerate(prices):
        if price["value_inc_vat"] < single_price:
            single_price = price["value_inc_vat"]
            single_start = datetime.strptime(price["valid_from"], "%Y-%m-%dT%H:%M:%SZ")
        try:
            this_group_price = price["value_inc_vat"] + prices[index + 1]["value_inc_vat"] + \
                               prices[index + 2]["value_inc_vat"]
            if this_group_price < group_price:
                group_price = this_group_price
                group_start = datetime.strptime(price["valid_from"], "%Y-%m-%dT%H:%M:%SZ")
        except IndexError:
            pass
    return {
        "cheapest_slot": single_start,
        "slot_price": single_price,
        "cheapest_group": group_start,
    }


def send_toot(start_at: datetime, data: Dict):
    text = (
        f"@frak@mastodon.org.uk For {start_at.strftime('%A %-d %B')} you should charge the batteries starting from "
        f"{data['cheapest_group'].strftime('%H:%M%p')}. The cheapest slot today is at "
        f"{data['cheapest_slot'].strftime('%H:%M%p')} and costs {data['slot_price']} pence per kWh."
    )
    masto_client.toot(text)


if __name__ == "__main__":
    gsp = get_gsp()
    start = datetime.now(tz=timezone.utc).replace(hour=0, minute=0, second=0) + timedelta(days=1)
    end = datetime.now(tz=timezone.utc).replace(hour=2, minute=0, second=0) + timedelta(days=3)
    prices = get_daily_prices(gsp, start, end)
    windows = get_cheapest_windows(prices)
    send_toot(start, windows)
