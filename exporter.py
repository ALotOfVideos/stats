#!/usr/bin/env python3

from datetime import datetime, timedelta, timezone
import json
import os
from crawler import StatsCrawler

class StatsCollector(object):

    def __init__(self, config):
        self.config = config
        self.crawler = StatsCrawler(self.config)
        self.last_updated_file = self.config.last_updated_file

        self.last_updated = { g: { str(m): None for m in mods.keys() } for g,mods in self.config.mods.items() }
        self.updated_flag = { g: dict() for g in self.config.mods.keys() }

        self.t = datetime.now()

        if os.path.isfile(self.last_updated_file):
            try:
                with open(self.last_updated_file, 'r') as f:
                    self.last_updated = json.load(f)
                for g,mod in self.last_updated.items():
                    for m,t in mod.items():
                        self.last_updated[g][m] = datetime.fromisoformat(t)
            except json.decoder.JSONDecodeError:
                os.remove(self.last_updated_file)

        self.update()

    def prepareModStats(self):
        for g,modlist in self.mod_stats.items():
            for mod,stats in modlist.items():
                m = str(mod)

                self.updated_flag[g][mod] = False
                lu = stats.get('last_updated')

                # skip if no timestamp found
                if lu is None:
                    continue

                lu = datetime.fromisoformat(lu)

                # skip if timestamp exists but isn't newer
                if self.last_updated.get(g).get(m) is not None and lu <= self.last_updated[g][m]:
                    continue


                for k in ['mod_page_views', 'mod_daily_counts']:
                    latest = sorted(stats[k].keys())
                    # ignore today
                    while (lu - timedelta(days=1)) <= datetime.fromisoformat(latest[-1]).replace(tzinfo=timezone.utc):
                        # shave off last
                        latest = latest[:-1]

                    # skip if not first run
                    if self.last_updated[g].get(m) is not None:
                        # keep only latest
                        latest = [latest[-1]]

                    stats[k] = { l: stats[k][l] for l in latest}

                self.updated_flag[g][mod] = True
                self.last_updated[g][m] = lu

    def update(self):
        now = datetime.now(tz=timezone.utc)
        self.endorsements, self.mod_stats, self.files_stats = self.crawler.getStats(now)

        self.prepareModStats()
        with open(self.last_updated_file, 'w') as f:
            d = { g: { m: t.isoformat() for m,t in mod.items() } for g,mod in self.last_updated.items() }
            json.dump(d, f)

        self.t = now
