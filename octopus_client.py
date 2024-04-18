from datetime import datetime
from typing import Any, Dict, List, Union

import requests
from pytz import timezone


class OctopusClient(object):
    """
    Adapted from https://gist.github.com/codeinthehole/5f274f46b5798f435e6984397f1abb64
    """

    BASE_URL = "https://api.octopus.energy/v1"
    tariff: Union[Dict[str, str], None] = None
    daily_prices: Union[List[Dict], None] = []

    class DataUnavailable(Exception):
        """
        Catch-all exception indicating we can't get data back from the API
        """

    def __init__(self, api_key: str, account_number: str):
        self._api_key: str = api_key
        self._session = requests.Session()
        self._get_tariff_details(account_number)

    def _get(self, path, params=None) -> Dict:
        """
        Make a GET HTTP request
        """
        if params is None:
            params = {}
        url = self.BASE_URL + path
        try:
            response = self._session.request(
                method="GET", url=url, auth=(self._api_key, ""), params=params
            )
        except requests.RequestException as e:
            raise self.DataUnavailable("Network exception") from e

        if response.status_code != 200:
            raise self.DataUnavailable(
                "Unexpected response status (%s)" % response.status_code
            )

        return response.json()

    def _agile_tariff_unit_rates(self, period_from: datetime) -> Dict:
        """
        Get unit rates for the given period
        See https://developer.octopus.energy/docs/api/#list-tariff-charges
        """
        if self.tariff is None:
            raise self.DataUnavailable("Please fetch account details before calling this method!")

        return self._get(
            f"/products/{self.tariff['product']}/electricity-tariffs/{self.tariff['code']}/standard-unit-rates/",
            params={"period_from": period_from.isoformat()},
        )

    def _user_account(self, account_number: str) -> Dict:
        return self._get(f"/accounts/{account_number}/")

    def _product_list(self, available_at: str) -> Dict:
        params = {"brand": "OCTOPUS_ENERGY", "is_variable": True, "available_at": available_at}
        return self._get(f"/products/", params)

    def _get_tariff_details(self, account_number: str) -> Dict[str, str]:
        if self.tariff is None:
            my_account = self._user_account(account_number)["properties"][0]
            import_point = None
            for meter_point in my_account["electricity_meter_points"]:
                if "is_export" in meter_point and not meter_point["is_export"]:
                    import_point = meter_point
                    break
            if import_point is None:
                raise self.DataUnavailable("Unable to find the import meter point!")

            active_agreement = None
            today = datetime.now(timezone("Europe/London"))
            for agreement in import_point["agreements"]:
                started_at = datetime.strptime(agreement["valid_from"], "%Y-%m-%dT%H:%M:%S%z")
                finished_at = datetime.strptime(agreement["valid_to"], "%Y-%m-%dT%H:%M:%S%z")
                if started_at < today < finished_at:
                    active_agreement = agreement
                    break
            if active_agreement is None:
                raise self.DataUnavailable("Unable to find an active agreement!")

            product = None
            prod_list = self._product_list(active_agreement["valid_from"])["results"]
            for item in prod_list:
                if item["code"] in active_agreement["tariff_code"]:
                    product = item

            self.tariff = {
                "mpan": import_point["mpan"],
                "product": product["code"],
                "code": active_agreement["tariff_code"],
            }

        return self.tariff

    def get_daily_prices(self, start_at: datetime) -> List[Dict[str, Any]]:
        if len(self.daily_prices) == 0:
            res = self._agile_tariff_unit_rates(start_at)["results"]
            if not res:
                raise RuntimeError(
                    "No prices returned, are you running this script before 4pm?"
                )
            self.daily_prices = sorted(res, key=lambda item: item["valid_from"])
        return self.daily_prices
