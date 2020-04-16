#!/usr/bin/env python3

import toml
import math
import os.path

def _getDelete(dict, key, var=None):
    r = dict.get(key, var)
    if key in dict:
        del dict[key]
    return r

class StatsConfig(object):
    apikey = None
    mods = dict() # { 'masseffect': {144: _categories_default}, 'masseffect2': {245: _categories_default}, 'masseffect3': {773: _categories_default} }
    _categories_all = ['main', 'update', 'optional', 'old_version', 'miscellaneous']
    _categories_default = _categories_all
    game_id_file = 'game-ids.json'
    _minInterval = 300
    _config_file_default = 'config.toml'
    last_updated_file = 'last-mod-stats-update.json'
    prom = { 'port': 8000 }
    timescaleDB = { 'dbname': 'nm-stats', 'user': 'nm-stats' }

    def __init__(self, config_file=_config_file_default):
        self._config_file = config_file
        if os.path.isfile(self._config_file):
            with open(self._config_file, 'r') as f:
                c = toml.load(f)
            self.apikey = _getDelete(c, 'apikey', self.apikey)
            self._categories_default = _getDelete(c, 'default categories', self._categories_all)
            self.game_id_file = _getDelete(c, 'game id file', self.game_id_file)
            self.last_updated_file = _getDelete(c, 'mod stats timestamp file', self.last_updated_file)
            self.setMinInterval(_getDelete(c, 'min update interval', self._minInterval))
            self.prom = _getDelete(c, 'prometheus', self.prom)
            self.timescaleDB = _getDelete(c, 'timescaleDB', self.timescaleDB)
            self.mods = c

        else:
            self.dumpConfig()

        self.updateInterval()
        self.formatModslist()
        self.games = self.mods.keys() # ['masseffect', 'masseffect2', 'masseffect3']
        if not self.validate():
            exit(1)

    @property
    def categories_default(self):
        return self._categories_default

    def formatModslist(self):
        # correct nesting of mods = dict(dict(list))
        # fill in self._categories_default
        try:
            temp = dict()
            for g,m in self.mods.items():
                if isinstance(m, int):
                    temp[g] = { m: self._categories_default }
                elif isinstance(m, list):
                    temp[g] = { int(modID): self._categories_default for modID in m }
                elif isinstance(m, dict):
                    temp[g] = dict()
                    for modID,cats in m.items():
                        if isinstance(cats, str):
                            if cats in ('default'):
                                temp[g][int(modID)] = self._categories_default
                            elif cats in ('all'):
                                temp[g][int(modID)] = self._categories_all
                            elif cats not in self._categories_all:
                                raise ValueError(f'Invalid category {c}. Available categories: {self._categories_all}.')
                            else:
                                temp[g][int(modID)] = [cats]
                        elif isinstance(cats, list):
                            if len(cats) > 0:
                                for c in cats:
                                    if not isinstance(c, str):
                                        raise TypeError(f'Categories must be given as strings. Given: {c} ({type(c)})')
                                    elif c not in self._categories_all:
                                        raise ValueError(f'Invalid category {c}. Available categories: {self._categories_all}.')
                                    temp[g][int(modID)] = cats
                            else:
                                temp[g][int(modID)] = self._categories_default
                        else:
                            raise TypeError(f'Mod categories must be either single string or list. Given: {cats} ({type(cats)})')

                else:
                    raise TypeError(f'Mods list has invalid format: per game either int, list or dict is needed. Given: {m} ({type(m)})')
            self.mods = temp

        except (TypeError, ValueError) as e:
            print(f'Mods section of {self._config_file} has invalid format.\nSee README.md and the example {self._config_file_default}.example.')
            raise e
        # except:
        #     raise Exception(f'Mods section of {self._config_file} has invalid format.\nSee README.md and the example {self._config_file_default}.example.')

    @property
    def interval(self):
        return self._interval

    def getTimescaleDBString(self):
        str = ''
        for k,v in self.timescaleDB.items():
            str += f"{k}={v} "
        return str[:-1]

    def setMinInterval(self,i):
        # 100 API requests per hour is the maximum allowed frequency
        # 60 min * 60 sec / 100 reqs = min 36 sec between reqs
        self._minInterval = max(36,i)
        self.updateInterval()

    def updateInterval(self):
        numMods = sum([len(x.keys()) for x in self.mods.values()])
        self._interval = max(self._minInterval, math.ceil(36 * 2 * numMods))

    def dumpConfig(self):
        with open(self._config_file, 'w') as f:
            c = dict()
            c['apikey'] = self.apikey
            c['game id file'] = self.game_id_file
            c['mod stats timestamp file'] = self.last_updated_file
            c['default categories'] = self._categories_default
            c['min update interval'] = self._minInterval
            c['prometheus'] = self.prom
            c['timescaleDB'] = self.timescaleDB
            for g,m in self.mods.items():
                temp = dict()
                for modID,cats in m.items():
                    temp[str(modID)] = cats
                c[g] = temp
            toml.dump(c, f)

    def validate(self):
        valid = True
        if self.apikey in (None, ''):
            print('No API key was given. Learn how to get your API key in README.md.')
            valid = False
        if len(self.mods) <= 0:
            print(f'No mods were given. Add at least one mod you want to track to {self._config_file}.')
            valid = False
        return valid
