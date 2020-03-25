#!/usr/bin/env python3

from prometheus_client.core import GaugeMetricFamily, REGISTRY
from prometheus_client import start_http_server
from datetime import datetime, timedelta, timezone
from time import time, sleep, strftime
import json
import os.path
from crawler import getStats

class ALOVCollector(object):
    last_updated = { 'masseffect': None, 'masseffect2': None, 'masseffect3': None }
    updated_flag = { 'masseffect': False, 'masseffect2': False, 'masseffect3': False }
    last_updated_file = 'last_mod_stats_update.json'

    def __init__(self):
        if os.path.isfile(self.last_updated_file):
            with open(self.last_updated_file, 'r') as f:
                self.last_updated = json.load(f)
            for g,t in self.last_updated.items():
                self.last_updated[g] = datetime.fromisoformat(t)
        else:
            self.last_updated = { 'masseffect': None, 'masseffect2': None, 'masseffect3': None }
        self.update()

    def prepareModStats(self):
        for n,g in self.mod_stats.items():
            self.updated_flag[n] = False
            lu = g.get('last_updated')

            # skip if no timestamp found
            if lu is None:
                continue

            lu = datetime.fromisoformat(lu)

            # skip if timestamp exists but isn't newer
            if self.last_updated[n] is not None and lu <= self.last_updated[n]:
                continue

            self.updated_flag[n] = True

            # skip if timestamp doesn't exist (first run)
            if self.last_updated[n] is None:
                self.last_updated[n] = lu
                continue

            self.last_updated[n] = lu

            for k in ['mod_page_views', 'mod_daily_counts']:
                latest = sorted(g[k].keys())
                # ignore today
                while (lu - timedelta(days=1)) >= datetime.fromisoformat(latest[-1]).replace(tzinfo=timezone.utc):
                    # shave off last
                    latest = latest[:-1]

                # keep only latest
                latest = latest[-1]
                g[k] = { latest: g[k][latest] }


    def update(self):
        t = datetime.now()
        self.endorsements, self.mod_stats, self.files_stats = getStats(t)

        self.prepareModStats()
        with open(self.last_updated_file, 'w') as f:
            d = { g: t.isoformat() for g,t in self.last_updated.items() }
            json.dump(d, f)

        self.timestamp = t.timestamp()

    def collect(self):
        for n,g in self.endorsements.items():
            end = GaugeMetricFamily(name=f'alov_{n}_endorsements', documentation=f'ALOV for {n} endorsements', value=g.get('endorsement_count', 0))
            yield end

        for n,g in self.mod_stats.items():
            if not self.updated_flag[n]:
                continue

            tdls = GaugeMetricFamily(name=f'alov_{n}_totaldownloads', documentation=f'ALOV for {n} total downloads (on Nexus Mods page)')
            tdls.add_metric(labels=[], value=g.get('total_downloads', 0), timestamp=self.last_updated[n].timestamp())
            page = GaugeMetricFamily(name=f'alov_{n}_pageviews', documentation=f'ALOV for {n} page views')
            ddls = GaugeMetricFamily(name=f'alov_{n}_dailydownloads', documentation=f'ALOV for {n} daily downloads (on Nexus Mods statistics page)')

            for day,views in g.get('mod_page_views', dict()).items():
                page.add_metric(labels=[], value=views, timestamp=datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp())
            for day,views in g.get('mod_daily_counts', dict()).items():
                ddls.add_metric(labels=[], value=views, timestamp=datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp())

            yield tdls
            yield page
            yield ddls

        for n,g in self.files_stats.items():
            l = ['name', 'version', 'category']
            dls = GaugeMetricFamily(name=f'alov_{n}_downloads', documentation=f'ALOV for {n} download counts', labels=l)
            unq = GaugeMetricFamily(name=f'alov_{n}_uniquedownloads', documentation=f'ALOV for {n} unique download counts', labels=l)
            sizes = GaugeMetricFamily(name=f'alov_{n}_sizes', documentation=f'File sizes ALOV for {n}', labels=l)

            for f,v in g.items():
                dls.add_metric(labels=[v.get('name', ''), v.get('version', ''), v.get('category_name', '')], value=v.get('downloads', 0), timestamp=self.timestamp)
                unq.add_metric(labels=[v.get('name', ''), v.get('version', ''), v.get('category_name', '')], value=v.get('unique_downloads', 0), timestamp=self.timestamp)
                sizes.add_metric(labels=[v.get('name', ''), v.get('version', ''), v.get('category_name', '')], value=v.get('size_kb', 0), timestamp=self.timestamp)

            yield dls
            yield unq
            yield sizes

collector = ALOVCollector()
REGISTRY.register(collector)

if __name__ == '__main__':
    # Start up the server to expose the metrics.
    port = 8000
    print(f'Starting HTTP server on port {port}')
    start_http_server(port)

    interval = 300
    print(f'Starting update loop every {interval} seconds')
    starttime=time()
    while True:
        sleep(interval - ((time() - starttime) % interval))
        print(f"{strftime('%c')}: polling stats update")
        collector.update()
