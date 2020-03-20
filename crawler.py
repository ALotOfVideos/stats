#!/usr/bin/env python3

import urllib.request as r
import json
import csv
from datetime import datetime

api = 'https://api.nexusmods.com'
game = ['masseffect', 'masseffect2', 'masseffect3']
gameid = dict()
alov = { 'masseffect': 144, 'masseffect2': 245, 'masseffect3': 773 }
endpoint = { 'files': '/v1/games/{:s}/mods/{:d}/files.json?category=main',
             'details': '/v1/games/{:s}/mods/{:d}/files/{:d}.json?category=main',
             'games': '/v1/games/{:s}.json' }
spoof = { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36' }
with open('api-key.txt', 'r') as f:
    headers = { 'accept': 'application/json',
                'apikey': f.read() }
files = { g: list() for g in game }
stats = { g: dict() for g in game }

if __name__ == '__main__':

    for g in game:
        url = api + endpoint['files'].format(g, alov[g])
        req = r.Request(url, headers=headers)
        response = r.urlopen(req)
        for f in json.loads(response.read()).get('files', []):
            # files[g].append({ 'g': g, 'a': a, 'f': f.get('file_id', 0) })
            files[g].append(f.get('file_id', 0))

        url = api + endpoint['games'].format(g)
        req = r.Request(url, headers=headers)
        response = r.urlopen(req)
        gameid[g] = json.loads(response.read()).get('id')

    # print(gameid)

    for g,v in files.items():
        filenames = dict()
        for i in v:
            url = api + endpoint['details'].format(g, alov[g], i)
            req = r.Request(url, headers=headers)
            response = r.urlopen(req)
            info = json.loads(response.read())
            del info["external_virus_scan_url"]
            del info["description"]
            filenames[i] = { 'name': info.get('name') }
        files[g] = filenames

    # print(files)

    timestamp = int(datetime.now().timestamp()*1000000//300000000)

    for g in game:
        with r.urlopen(r.Request('https://staticstats.nexusmods.com/live_download_counts/files/{:d}.csv?cachesteamp={:d}'.format(gameid[g],timestamp), headers=spoof)) as dl_csv:
            dl_csv = dl_csv.read().decode('utf-8')
            for row in csv.reader(dl_csv.split('\n')):
                if len(row) < 3:
                    continue
                stats[g][int(row[0])] = { 'downloads': row[1], 'unique_downloads': row[2]}

    for g,f in files.items():
        # print(stats[g])
        for i,v in f.items():
            v.update(stats[g][i])

    for n,g in files.items():
        print(n)
        for f,v in g.items():
            print('\t', v)
