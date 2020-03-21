#!/usr/bin/env python3

from prometheus_client.core import GaugeMetricFamily, REGISTRY
from prometheus_client import start_http_server
from datetime import datetime
from time import time, sleep
from crawler import getStats

class ALOVCollector(object):
    def __init__(self):
        self.update()

    def update(self):
        t = datetime.now()
        self.data = getStats(t)
        self.timestamp = t.timestamp()

    def collect(self):
        for n,g in self.data.items():
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

    interval = 900
    print(f'Starting update loop every {interval} seconds')
    starttime=time()
    while True:
        sleep(interval - ((time() - starttime) % interval))
        collector.update()
