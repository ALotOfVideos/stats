#!/usr/bin/env python3

import urllib.request as r
import urllib.error
import json
import os.path
import csv
from datetime import datetime

class StatsCrawler:

    def __init__(self, config):
        self.config = config
        self.api = 'https://api.nexusmods.com'
        self.dl_stats_csv = 'https://staticstats.nexusmods.com/live_download_counts/files/{:d}.csv?cachesteamp={:d}'
        self.mod_stats_json = 'https://staticstats.nexusmods.com/mod_monthly_stats/{:d}/{:d}.json'

        self.endpoint = { 'files': '/v1/games/{:s}/mods/{:d}/files.json?category={:s}',
                          'details': '/v1/games/{:s}/mods/{:d}/files/{:d}.json',
                          'games': '/v1/games/{:s}.json',
                          'mod': '/v1/games/{:s}/mods/{:d}.json' }
        self.spoof = { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36' }

        self.games = self.config.games
        self.mods = self.config.mods
        self.headers = { 'accept': 'application/json', 'apikey': self.config.apikey }
        self.game_id_file = self.config.game_id_file
        self.gameid = self.getGameIDs()

    def getGameIDs(self):
        if os.path.isfile(self.game_id_file):
            with open(self.game_id_file, 'r') as f:
                gameid = json.load(f)
        else:
            gameid = dict()
            for g in self.games:
                # get game id for later
                url = self.api + self.endpoint['games'].format(g)
                req = r.Request(url, headers=self.headers)
                response = r.urlopen(req)
                gameid[g] = json.loads(response.read()).get('id')

            with open(self.game_id_file, 'w') as f:
                json.dump(gameid, f)

        return gameid

    def getStats(self, time=datetime.now()):
        endorsements = { g: dict() for g in self.games }
        files = { g: { m: dict() for m in self.mods[g] } for g in self.games }
        stats = { g: dict() for g in self.games }
        mod_stats = { g: dict() for g in self.games }

        for g in self.games:
            for m in self.mods[g].keys():
                try:
                    # get mod stats
                    url = self.api + self.endpoint['mod'].format(g, m)
                    req = r.Request(url, headers=self.headers)
                    response = r.urlopen(req)
                    endorsements[g][m] = json.loads(response.read())
                except urllib.error.HTTPError as e:
                    print(e)

        for g in self.games:
            for m,categories in self.mods[g].items():
                try:
                    # get list of files
                    url = self.api + self.endpoint['files'].format(g, m, ','.join(categories))
                    req = r.Request(url, headers=self.headers)
                    response = r.urlopen(req)
                    l = json.loads(response.read()).get('files', [])
                    for f in l:
                        files[g][m][f.get('file_id', 0)] = f
                except urllib.error.HTTPError as e:
                    print(e)

        # match nexus' cache busting timestamp format
        timestamp = int(time.timestamp() * 1000000 / 300000000)

        for g in self.games:
            # get download stats
            with r.urlopen(r.Request(self.dl_stats_csv.format(self.gameid[g],timestamp), headers=self.spoof)) as dl_csv:
                # decode binary format
                dl_csv = dl_csv.read().decode('utf-8').split('\n')
                for row in csv.reader(dl_csv):
                    # remove lines that don't match the expected id,dls,unique format
                    if len(row) < 3:
                        continue
                    stats[g][int(row[0])] = { 'downloads': int(row[1]), 'unique_downloads': int(row[2])}

        # fill info in with file details
        for g,mod in files.items():
            for m,f in mod.items():
                for i,v in f.items():
                    v.update(stats[g][i])

        for g in self.games:
            for m in self.mods[g]:
                # get mod stats
                url = self.mod_stats_json.format(self.gameid[g],m)
                req = r.Request(url, headers=self.spoof)
                dl_json = r.urlopen(req)
                mod_stats[g][m] = json.loads(dl_json.read())

        return endorsements, mod_stats, files

if __name__ == '__main__':
    from config import StatsConfig
    from pprint import pprint

    config = StatsConfig()
    crawler = StatsCrawler(config)

    endorsements, mod_stats, files_stats = crawler.getStats()

    pprint(endorsements)

    print()

    pprint(mod_stats)

    print()

    for n,g in files_stats.items():
        print('\n', n)
        for f,v in g.items():
            pprint(v)
