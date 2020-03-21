#!/usr/bin/env python3

import urllib.request as r
import json
import csv
from datetime import datetime

api = 'https://api.nexusmods.com'
stats_csv = 'https://staticstats.nexusmods.com/live_download_counts/files/{:d}.csv?cachesteamp={:d}'
game = ['masseffect', 'masseffect2', 'masseffect3']
gameid = dict()
alov = { 'masseffect': 144, 'masseffect2': 245, 'masseffect3': 773 }
categories = ['main', 'update', 'optional', 'old_version', 'miscellaneous']
endpoint = { 'files': '/v1/games/{:s}/mods/{:d}/files.json?category={:s}',
             'details': '/v1/games/{:s}/mods/{:d}/files/{:d}.json',
             'games': '/v1/games/{:s}.json' }
spoof = { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36' }
with open('api-key.txt', 'r') as f:
    headers = { 'accept': 'application/json',
                'apikey': f.read() }

def getStats(time=datetime.now()):
    files = { g: dict() for g in game }
    stats = { g: dict() for g in game }

    for g in game:
        # get list of files
        url = api + endpoint['files'].format(g, alov[g], ','.join(categories))
        req = r.Request(url, headers=headers)
        response = r.urlopen(req)
        l = json.loads(response.read()).get('files', [])
        for f in l:
            files[g][f.get('file_id', 0)] = f

        # get game id for later
        url = api + endpoint['games'].format(g)
        req = r.Request(url, headers=headers)
        response = r.urlopen(req)
        gameid[g] = json.loads(response.read()).get('id')


    # match nexus' cache busting timestamp format
    timestamp = int(time.timestamp() * 1000000 / 300000000)

    for g in game:
        # get download stats
        with r.urlopen(r.Request(stats_csv.format(gameid[g],timestamp), headers=spoof)) as dl_csv:
            # decode binary format
            dl_csv = dl_csv.read().decode('utf-8').split('\n')
            for row in csv.reader(dl_csv):
                # remove lines that don't match the expected id,dls,unique format
                if len(row) < 3:
                    continue
                stats[g][int(row[0])] = { 'downloads': int(row[1]), 'unique_downloads': int(row[2])}

    # fill info in with file details
    for g,f in files.items():
        for i,v in f.items():
            v.update(stats[g][i])

    return files

if __name__ == '__main__':
    files = getStats()
    for n,g in files.items():
        print(n)
        for f,v in g.items():
            print('\t', v)
