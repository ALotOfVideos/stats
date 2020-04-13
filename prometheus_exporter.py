#!/usr/bin/env python3

from prometheus_client.core import GaugeMetricFamily, REGISTRY
from prometheus_client import start_http_server
from datetime import datetime, timezone
from time import time, sleep, strftime
import re
from config import StatsConfig
from exporter import StatsCollector

clean_alnum = re.compile(r'[^a-z0-9]')

class PrometheusStatsColletor(StatsCollector):

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
                tdls.add_metric(labels=[], value=stats.get('total_downloads', 0), timestamp=self.last_updated[g][str(m)].timestamp())
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
                    dls.add_metric(labels=[v.get('name', ''), v.get('version', ''), v.get('category_name', '')], value=v.get('downloads', 0), timestamp=self.t.timestamp())
                    unq.add_metric(labels=[v.get('name', ''), v.get('version', ''), v.get('category_name', '')], value=v.get('unique_downloads', 0), timestamp=self.t.timestamp())
                    sizes.add_metric(labels=[v.get('name', ''), v.get('version', ''), v.get('category_name', '')], value=v.get('size_kb', 0), timestamp=self.t.timestamp())

                yield dls
                yield unq
                yield sizes

    def getModName(self, default, game=None, modid=None, endorsements=None):
        if endorsements is None:
            assert game is not None and modid is not None
            endorsements = self.endorsements.get(game, default).get(modid, default)
        name = endorsements.get('name', default)
        return name, clean_alnum.sub('', name.lower())

if __name__ == '__main__':
    cfg = StatsConfig()
    collector = PrometheusStatsColletor(cfg)
    REGISTRY.register(collector)

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
