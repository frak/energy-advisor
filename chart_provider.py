import os
from datetime import datetime

import pandas as pa
import plotly.express as px
from uuid import uuid4

from pytz import timezone

from octopus_client import OctopusClient


class ChartProvider:
    TWO_HOURS = 7200000

    def __init__(self, client: OctopusClient):
        self._client = client
        self._filename: str = ""

    def make_chart(self, start: datetime) -> str:
        data = self._client.get_daily_prices(start)
        for item in data:
            valid_from = datetime.strptime(item["valid_from"], "%Y-%m-%dT%H:%M:%S%z")
            item["valid_from"] = valid_from.astimezone(timezone("Europe/London")).strftime("%Y-%m-%dT%H:%M:%S%z")
        df = pa.DataFrame(data)
        fig = px.bar(
            df, y="value_inc_vat", x="valid_from",
            color="value_inc_vat",
            color_continuous_scale=[
                (0, "chartreuse"), (0.05, "chartreuse"),
                (0.05, "seagreen"), (0.1, "seagreen"),
                (0.1, "orange"), (0.8, "orange"),
                (0.8, "crimson"), (1, "crimson"),
            ],
            width=1024, height=768,
        )
        fig.update_layout(
            coloraxis_showscale=False,
            yaxis=None,
            xaxis=None,
            margin={'l': 3, 'r': 3, 't': 3, 'b': 3},
        )
        fig.update_xaxes(showgrid=False, ticklabelmode="period", dtick=self.TWO_HOURS)
        fig.update_yaxes(showgrid=False)
        self._filename = f"/tmp/{uuid4()}.png"
        fig.write_image(self._filename)
        return self._filename

    def delete_chart(self) -> None:
        if self._filename:
            os.remove(self._filename)
