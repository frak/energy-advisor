import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Union

from jinja2 import Environment, FileSystemLoader
from mastodon import Mastodon

from chart_provider import ChartProvider
from octopus_client import OctopusClient
from daily_price_provider import DailyPriceProvider
from solar_provider import SolarProvider

# Octopus
OCTOPUS_TOKEN = os.getenv("OCTOPUS_TOKEN")
MPAN = os.getenv("MPAN")

# Mastodon
MASTO_TOKEN = os.getenv("MASTO_TOKEN")
BOT_HOME = os.getenv("BOT_HOME", "https://botsin.space")
SEND_TOOT_TO = os.getenv("SEND_TOOT_TO")

# Debug
SEND_TOOTS = os.getenv("SEND_TOOTS", "no")


def send_toot(octo_data: Dict[str, Any], solar_data: Dict[str, Union[int, float]], chart_filename: str):
    masto_client = Mastodon(access_token=MASTO_TOKEN, api_base_url=BOT_HOME)
    masto_image = masto_client.media_post(chart_filename, synchronous=True)
    environment = Environment(
        loader=FileSystemLoader(
            f"{os.path.dirname(os.path.realpath(__file__))}/templates/"
        )
    )
    template = environment.get_template("message.txt.tmpl")
    tomorrow = octo_data["run_for"] + timedelta(days=1)
    template_data = {
        "username": SEND_TOOT_TO,
        "date": octo_data["run_for"].strftime("%-d")
        + "-"
        + tomorrow.strftime("%-d %B"),
        "start_time": octo_data["cheapest_group"].strftime("%H:%M%p"),
        "cheapest_slot": octo_data["cheapest_slot"].strftime("%H:%M%p"),
        "cheapest_price": octo_data["slot_price"],
        "has_solar": False,
    }
    if solar_data:
        template_data["has_solar"] = True
        template_data["mean_forecast"] = f"{round(solar_data['mean'] / 1000, 1)}kWh"
        template_data["max_forecast"] = f"{round(solar_data['max'] / 1000, 1)}kWh"
        template_data["min_forecast"] = f"{round(solar_data['min'] / 1000, 1)}kWh"
        template_data["data_points"] = solar_data["count"]
    text = template.render(template_data)
    if SEND_TOOTS == "yes":
        masto_client.status_post(text, media_ids=[masto_image])
    else:
        print(f"Message to send: {text}")


if __name__ == "__main__":
    if OCTOPUS_TOKEN is None or MPAN is None or MASTO_TOKEN is None or SEND_TOOT_TO is None:
        print(
            f"Required env vars are missing, please check: {OCTOPUS_TOKEN=}, {MPAN=}, {MASTO_TOKEN=}, {SEND_TOOT_TO=}"
        )
        exit(1)
    start = datetime.now(tz=timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=23)
    solar_start = datetime.now(tz=timezone.utc).replace(hour=0, minute=0, second=0) + timedelta(days=1)

    octo_client = OctopusClient(OCTOPUS_TOKEN, MPAN)
    octopus = DailyPriceProvider(octo_client)
    charts = ChartProvider(octo_client)
    solar = SolarProvider()
    send_toot(
        octopus.get_price_windows(start),
        solar.get_mean_and_range_for_date(solar_start.strftime("%Y-%m-%d")),
        charts.make_chart(start),
    )
    charts.delete_chart()
