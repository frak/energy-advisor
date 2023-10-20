# Energy Watcher

A python script that fetches tomorrow's price data from the Octopus Agile
tariff and looks for the cheapest 90-minute window for charging a battery.

It can also track the solar forecast for your installation and give you a
summary of the data for the last 24 hours.

## Installation

Clone this repo onto your system and install the requirements with `pip install -r requirements.txt`

Find the values for the required environment variables:

- `OCTOPUS_TOKEN` - this is your Octopus API token, found on the [Octopus Developer Dashboard](https://octopus.energy/dashboard/new/accounts/personal-details/api-access).
- `MPAN` - your electricity meterpoint MPAN, also found on the [Octopus Developer Dashboard](https://octopus.energy/dashboard/new/accounts/personal-details/api-access).
- `MASTO_TOKEN` - your Mastodon client access token. Follow [the official documentation](https://docs.joinmastodon.org/client/token/) for help setting that up. 
- `BOT_HOME` - the base URL for the Mastodon account that will be posting. This defaults to https://botsin.space.
- `SEND_TOOTS` - in order for your toots to be sent this **MUST** be set to `yes`. This is to avoid sending toots when debugging.
- `SEND_TOOT_TO` - who you want to receive the toot.

Next create a crontab entry to schedule the running of the script, this also sets the required environment variables 
that the script needs:
```cronexp
OCTOPUS_TOKEN=api-token
MPAN=0123456789
MASTO_TOKEN=masto-access-token
BOT_HOME=https://botsin.space
SEND_TOOTS=yes
SEND_TOOT_TO=@recipient@host.com
0 20 * * * /usr/bin/python /path/to/repo/main.py 2>&1
```

### Optional solar forecast reporting

You need to locate the values for the following environment variables: `LAT`, `LNG`, `DEC`, `AZ`, `KWP`. These values 
and how to determine them are amply described on the [Forecast.Solar](https://doc.forecast.solar/api:estimate) web-site.
The API updates every 15 minutes, so there is no point in querying more frequently than that, but you can definitely
pick larger intervals if it suits you.

__NOTE:__ This functionality uses the public Forecast.Solar API and will count against your quota if you use Home Assistant
or some other service that uses this API.

```cronexp
LAT=your-lat
LNG=your-lng
DEC=your-declination
AZ=your-azimuth
KWP=your-kwp
*/15 * * * * /usr/bin/python /path/to/repo/collector.py 2>&1
```

Profit!

## Customisation

The template for the message is stored in `templates/message.txt.tmpl` and can be customised as you see fit.