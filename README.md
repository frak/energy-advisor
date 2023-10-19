# Energy Watcher

A simple python script that fetches tomorrow's price data from the Octopus Agile
tariff and looks for the cheapest 90-minute window for charging a battery.

## Installation

Clone this repo onto your system and install the requirements with `pip install -r requirements.txt`

Find the values for the required environment variables:

- `OCTOPUS_TOKEN` - this is your Octopus API token, found on the [Octopus Developer Dashboard](https://octopus.energy/dashboard/new/accounts/personal-details/api-access).
- `MPAN` - your electricity meterpoint MPAN, also found on the [Octopus Developer Dashboard](https://octopus.energy/dashboard/new/accounts/personal-details/api-access).
- `MASTO_TOKEN` - your Mastodon client access token. Follow [the official documentation](https://docs.joinmastodon.org/client/token/) for help setting that up. 
- `BOT_HOME` - the base URL for the Mastodon account that will be posting. This defaults to https://botsin.space.
- `SEND_TOOTS` - in order for your toots to be sent this **MUST** be set to `yes`. This is to avoid sending toots when debugging.

Next create a crontab entry to schedule the running of the script, this also sets the required environment variables 
that the script needs:
```cronexp
OCTOPUS_TOKEN=api-token
MPAN=0123456789
MASTO_TOKEN=masto-access-token
BOT_HOME=https://botsin.space
SEND_TOOTS=yes
0 20 * * * /usr/bin/python /path/to/repo/main.py 2>&1
```

Profit!