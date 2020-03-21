# ALOV stats

Collects and tracks stats of ALOV downloads from Nexus Mods.

## Installation

1. `pip install prometheus_client`. Consider using a virtual environment.
1. Get an API key from https://www.nexusmods.com/users/myaccount?tab=api.
1. Save the API key in a text file called `api-key.txt` next to `crawler.py` (take care that nobody but you can access your API key).

## Usage

To print stats to stdout, run `./crawler.py`

To export metrics to [Prometheus](https://prometheus.io) and display with [Grafana](https://grafana.com/):
1. Run `./prometheus_exporter.py` as a daemon.
1. Set Prometheus to scrape from the running script (default `localhost:8000`) with scrape interval matching the script's (default 900 seconds).
1. Set up your Grafana dashboards using the provided metrics and labels (name, version, category). Example: `alov_masseffect3_uniquedownloads{name!~".*Unpacker.*",category="MAIN"}`
