import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict

from jinja2 import Environment, FileSystemLoader
from mastodon import Mastodon

from octopus_client import OctopusClient

# Octopus
OCTOPUS_TOKEN = os.getenv("OCTOPUS_TOKEN", None)
MPAN = os.getenv("MPAN", None)

# Mastodon
MASTO_TOKEN = os.getenv("MASTO_TOKEN", None)
BOT_HOME = os.getenv("BOT_HOME", "https://botsin.space")
SEND_TOOT_TO = os.getenv("SEND_TOOT_TO")

# Debug
SEND_TOOTS = os.getenv("SEND_TOOTS", "no")


octo_client = OctopusClient(OCTOPUS_TOKEN)
masto_client = Mastodon(access_token=MASTO_TOKEN, api_base_url=BOT_HOME)


def get_gsp() -> str:
    return octo_client.electricity_meter_point(MPAN)["gsp"][1:]


def get_daily_prices(gsp: str, start_at: datetime):
    res = octo_client.agile_tariff_unit_rates(gsp, period_from=start_at)["results"]
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
    environment = Environment(loader=FileSystemLoader(f"{os.path.dirname(os.path.realpath(__file__))}/templates/"))
    template = environment.get_template("message.txt.tmpl")
    data = {
        "username": SEND_TOOT_TO,
        "date": start_at.strftime('%A %-d %B'),
        "start_time": data['cheapest_group'].strftime('%H:%M%p'),
        "cheapest_slot": data['cheapest_slot'].strftime('%H:%M%p'),
        "cheapest_price": data['slot_price']
    }
    text = template.render(data)
    if SEND_TOOTS == "yes":
        masto_client.toot(text)
    else:
        print(f"Message to send: {text}")


if __name__ == "__main__":
    if OCTOPUS_TOKEN is None or MPAN is None or MASTO_TOKEN is None or SEND_TOOT_TO is None:
        print(
            f"Required env vars are missing, please check: {OCTOPUS_TOKEN=}, {MPAN=}, {MASTO_TOKEN=}, {SEND_TOOT_TO=}"
        )
        exit(1)

    gsp = get_gsp()
    start = datetime.now(tz=timezone.utc).replace(hour=0, minute=0, second=0) + timedelta(days=1)
    day_prices = get_daily_prices(gsp, start)
    windows = get_cheapest_windows(day_prices)
    send_toot(start, windows)
