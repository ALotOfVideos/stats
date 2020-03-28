#!/usr/bin/env python3

from prometheus_client.core import GaugeMetricFamily, REGISTRY
from prometheus_client import start_http_server
from datetime import datetime, timedelta, timezone
from time import time, sleep, strftime
import json
import os
import re
from config import StatsConfig
from crawler import StatsCrawler

clean_alnum = re.compile(r'[^a-z0-9]')

class StatsCollector(object):

    def __init__(self, config):
        self.config = config
        self.crawler = StatsCrawler(self.config)
        self.last_updated_file = self.config.last_updated_file

        self.last_updated = { g: { m: None for m in mods.keys() } for g,mods in self.config.mods.items() }
        self.updated_flag = { g: dict() for g in self.config.mods.keys() }

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
                if self.last_updated[g][m] is not None and lu <= self.last_updated[g][m]:
                    continue

                self.updated_flag[g][mod] = True

                # skip if timestamp doesn't exist (first run)
                if self.last_updated[g][m] is None:
                    self.last_updated[g][m] = lu
                    continue

                self.last_updated[g][m] = lu

                for k in ['mod_page_views', 'mod_daily_counts']:
                    latest = sorted(stats[k].keys())
                    # ignore today
                    while (lu - timedelta(days=1)) <= datetime.fromisoformat(latest[-1]).replace(tzinfo=timezone.utc):
                        # shave off last
                        latest = latest[:-1]

                    # keep only latest
                    latest = latest[-1]
                    g[k] = { latest: g[k][latest] }

    def update(self):
        t = datetime.now()
        self.endorsements, self.mod_stats, self.files_stats = self.crawler.getStats(t)

        self.prepareModStats()
        with open(self.last_updated_file, 'w') as f:
            d = { g: { m: t.isoformat() for m,t in mod.items() } for g,mod in self.last_updated.items() }
            json.dump(d, f)

        self.timestamp = t.timestamp()

    def getModName(self, default, game=None, modid=None, endorsements=None):
        if endorsements is None:
            assert game is not None and modid is not None
            endorsements = self.endorsements.get(game, default).get(modid, default)
        name = endorsements.get('name', default)
        return name, clean_alnum.sub('', name.lower())

    def collect(self):
        for g,mods in self.endorsements.items():
            for m,e in mods.items():
                fullname, name = self.getModName(endorsements=e, default=m)
                end = GaugeMetricFamily(name=f'{g}_{name}_endorsements', documentation=f'({g}) {fullname} endorsements', value=e.get('endorsement_count', 0))
                yield end

        for g,mods in self.mod_stats.items():
            for m,stats in mods.items():
                if not self.updated_flag[g][m]:
                    continue

                fullname, name = self.getModName(game=g, modid=m, default=m)

                tdls = GaugeMetricFamily(name=f'{g}_{name}_totaldownloads', documentation=f'({g}) {fullname} total downloads (on Nexus Mods page)')
                tdls.add_metric(labels=[], value=g.get('total_downloads', 0), timestamp=self.last_updated[g][str(m)].timestamp())
                page = GaugeMetricFamily(name=f'{g}_{name}_pageviews', documentation=f'({g}) {fullname} page views')
                ddls = GaugeMetricFamily(name=f'{g}_{name}_dailydownloads', documentation=f'({g}) {fullname} daily downloads (on Nexus Mods statistics page)')

                for day,views in stats.get('mod_page_views', dict()).items():
                    page.add_metric(labels=[], value=views, timestamp=datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp())
                for day,views in stats.get('mod_daily_counts', dict()).items():
                    ddls.add_metric(labels=[], value=views, timestamp=datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp())

                yield tdls
                yield page
                yield ddls

        l = ['name', 'version', 'category']
        for g,mods in self.files_stats.items():
            for m,stats in mods.items():
                fullname, name = self.getModName(game=g, modid=m, default=m)

                dls = GaugeMetricFamily(name=f'{g}_{name}_downloads', documentation=f'({g}) {fullname} download counts', labels=l)
                unq = GaugeMetricFamily(name=f'{g}_{name}_uniquedownloads', documentation=f'({g}) {fullname} unique download counts', labels=l)
                sizes = GaugeMetricFamily(name=f'{g}_{name}_sizes', documentation=f'({g}) {fullname} file sizes', labels=l)

                for f,v in stats.items():
                    dls.add_metric(labels=[v.get('name', ''), v.get('version', ''), v.get('category_name', '')], value=v.get('downloads', 0), timestamp=self.timestamp)
                    unq.add_metric(labels=[v.get('name', ''), v.get('version', ''), v.get('category_name', '')], value=v.get('unique_downloads', 0), timestamp=self.timestamp)
                    sizes.add_metric(labels=[v.get('name', ''), v.get('version', ''), v.get('category_name', '')], value=v.get('size_kb', 0), timestamp=self.timestamp)

                yield dls
                yield unq
                yield sizes

cfg = StatsConfig()
collector = StatsCollector(cfg)
REGISTRY.register(collector)

if __name__ == '__main__':
    # Start up the server to expose the metrics.
    port = cfg.prom.get('port', 8000)
    print(f'Starting HTTP server on port {port}')
    start_http_server(port)

    i = cfg.interval
    print(f'Starting update loop every {i} seconds')
    starttime=time()
    while True:
        sleep(i - ((time() - starttime) % i))
        print(f"{strftime('%c')}: polling stats update")
        collector.update()
