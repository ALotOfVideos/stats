# ALOV stats

Collects and tracks stats of ALOV downloads from Nexus Mods.

## Installation

1. Install dependencies: `pip install prometheus_client toml`. Consider using a [virtual environment](https://docs.python.org/3/tutorial/venv.html).
1. Copy `config.toml.example` to `config.toml`. Modify it to your needs and list the games and mods you want to track. Start a new section for each game: `[masseffect]`. Then list the mod IDs and file categories 
1. Get an API key from https://www.nexusmods.com/users/myaccount?tab=api and save it to your `config.toml`. Take care that nobody but you can access your API key!

## Usage

To print stats to stdout, run `./crawler.py`

To export metrics to [Prometheus](https://prometheus.io):
1. Run `./prometheus_exporter.py` as a daemon.
1. Set Prometheus to scrape from the running script (default `localhost:8000`) with scrape interval matching the script's `"min update interval"`.

To display metrics with [Grafana](https://grafana.com/):
1. Set up your Grafana dashboards using the provided metrics and labels (name, version, category). Prometheus example: `alov_masseffect3_uniquedownloads{name!~".*Unpacker.*",category="MAIN"}`