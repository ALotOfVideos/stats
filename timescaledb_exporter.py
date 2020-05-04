#!/usr/bin/env python3

import psycopg2
from time import time, sleep, strftime
from config import StatsConfig
from exporter import StatsCollector

class TimescaleDBStatsCollector(StatsCollector):
    _tablesCreated = False

    def __init__(self, config, conn):
        self.conn = conn
        super().__init__(config)

    def _createTables(self):
        if self._tablesCreated:
            return
        self._tablesCreated = True
        # create tables if not exists, and convert to timescaledb hypertables
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
                curs.execute("""CREATE TABLE IF NOT EXISTS games (
                                gameid  INTEGER     PRIMARY KEY,
                                game    TEXT        UNIQUE NOT NULL
                                );""")
                curs.execute("""CREATE TABLE IF NOT EXISTS mods (
                                gameid      INTEGER     REFERENCES games ON DELETE RESTRICT,
                                modid       INTEGER     NOT NULL,
                                mod         TEXT        NOT NULL,
                                picture_url TEXT                ,
                                PRIMARY KEY (gameid, modid)
                                );""")
                curs.execute("""CREATE TABLE IF NOT EXISTS endorsements (
                                gameid          INTEGER     REFERENCES games ON DELETE RESTRICT,
                                modid           INTEGER     NOT NULL,
                                endorsements    INTEGER     NOT NULL,
                                time            TIMESTAMPTZ NOT NULL,
                                FOREIGN KEY (gameid, modid) REFERENCES mods (gameid, modid) ON DELETE RESTRICT,
                                PRIMARY KEY (gameid, modid, time)
                                );""")
                curs.execute("SELECT create_hypertable('endorsements', 'time', if_not_exists => TRUE);")
                curs.execute("""CREATE TABLE IF NOT EXISTS nexus_mod_stats_total (
                                gameid          INTEGER     REFERENCES games ON DELETE RESTRICT,
                                modid           INTEGER     NOT NULL,
                                totaldls        INTEGER     NOT NULL,
                                time            TIMESTAMPTZ NOT NULL,
                                FOREIGN KEY (gameid, modid) REFERENCES mods (gameid, modid) ON DELETE RESTRICT,
                                PRIMARY KEY (gameid, modid, time)
                                );""")
                curs.execute("SELECT create_hypertable('nexus_mod_stats_total', 'time', if_not_exists => TRUE);")
                curs.execute("""CREATE TABLE IF NOT EXISTS nexus_mod_stats_daily (
                                gameid          INTEGER     REFERENCES games ON DELETE RESTRICT,
                                modid           INTEGER     NOT NULL,
                                pageviews       INTEGER     NOT NULL,
                                dailydls        INTEGER     NOT NULL,
                                time            DATE        NOT NULL,
                                FOREIGN KEY (gameid, modid) REFERENCES mods (gameid, modid) ON DELETE RESTRICT,
                                PRIMARY KEY (gameid, modid, time)
                                );""")
                curs.execute("SELECT create_hypertable('nexus_mod_stats_daily', 'time', if_not_exists => TRUE);")
                curs.execute("""CREATE TABLE IF NOT EXISTS nexus_mod_files (
                                gameid          INTEGER     REFERENCES games ON DELETE RESTRICT,
                                modid           INTEGER     NOT NULL,
                                fileid          INTEGER     NOT NULL,
                                modversion      TEXT        NOT NULL,
                                uploaded_time   TIMESTAMPTZ NOT NULL,
                                filename        TEXT        NOT NULL,
                                filesizekb      INTEGER     NOT NULL,
                                FOREIGN KEY (gameid, modid) REFERENCES mods (gameid, modid) ON DELETE RESTRICT,
                                PRIMARY KEY (gameid, modid, fileid)
                                );""")
                curs.execute("""CREATE TABLE IF NOT EXISTS nexus_mod_files_stats (
                                gameid          INTEGER     REFERENCES games ON DELETE RESTRICT,
                                modid           INTEGER     NOT NULL,
                                fileid          INTEGER     NOT NULL,
                                category        TEXT        NOT NULL,
                                dls             INTEGER     NOT NULL,
                                uniquedls       INTEGER     NOT NULL,
                                time            TIMESTAMPTZ NOT NULL,
                                FOREIGN KEY (gameid, modid) REFERENCES mods (gameid, modid) ON DELETE RESTRICT,
                                FOREIGN KEY (gameid, modid, fileid) REFERENCES nexus_mod_files (gameid, modid, fileid) ON DELETE RESTRICT,
                                PRIMARY KEY (gameid, modid, fileid, time)
                                );""")
                curs.execute("SELECT create_hypertable('nexus_mod_files_stats', 'time', if_not_exists => TRUE);")
                # curs.execute("CREATE TABLE IF NOT EXISTS nextcloud_files ();")
                # curs.execute("CREATE TABLE IF NOT EXISTS nextcloud_files_stats ();")
                # curs.execute("SELECT create_hypertable('nextcloud_files_stats', 'time', if_not_exists => TRUE);")

    def _insertMods(self):
        with self.conn:
            with self.conn.cursor() as curs:

                # insert mod info if not exists
                gamequery = 'INSERT INTO games VALUES (%s, %s) ON CONFLICT DO NOTHING;'
                for name,id in self.crawler.gameid.items():
                            curs.execute(gamequery, (id, name))

                modquery = 'INSERT INTO mods VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING;'
                for g,mods in self.endorsements.items():
                    for m,e in mods.items():
                        if e.get('name') is not None and e.get('picture_url') is not None:
                            curs.execute(modquery, (self.crawler.gameid[g], m, e['name'], e['picture_url']))

    def collect(self):
        self._createTables()
        self._insertMods()

        # endorsements
        queryendorse = 'INSERT INTO endorsements VALUES (%(gameid)s, %(modid)s, %(endorsements)s, %(time)s);'
        with self.conn:
            with self.conn.cursor() as curs:
                for g,mods in self.endorsements.items():
                    for m,e in mods.items():
                        data = { 'gameid': e['game_id'],
                                 'modid' : e['mod_id'],
                                 'endorsements' : e['endorsement_count'],
                                 'time': self.t
                                }
                        curs.execute(queryendorse, data)

        querytotal = 'INSERT INTO nexus_mod_stats_total VALUES (%(gameid)s, %(modid)s, %(totaldls)s, %(time)s) ON CONFLICT DO NOTHING;'
        querydaily = 'INSERT INTO nexus_mod_stats_daily VALUES (%(gameid)s, %(modid)s, %(pageviews)s, %(dailydls)s, %(time)s) ON CONFLICT DO NOTHING;'
        with self.conn:
            with self.conn.cursor() as curs:
                for g,mods in self.mod_stats.items():
                    for m,stats in mods.items():
                        if not self.updated_flag[g][m]:
                            continue

                        data = { 'gameid': self.crawler.gameid[g],
                                 'modid': m,
                                 'totaldls': stats.get('total_downloads', 0),
                                 'time': self.last_updated[g][str(m)]
                                }
                        curs.execute(querytotal, data)

                        for date in set(list(stats.get('mod_page_views', dict()).keys()) + list(stats.get('mod_daily_counts', dict()).keys())):
                            data = { 'gameid': self.crawler.gameid[g],
                                     'modid': m,
                                     'pageviews': stats.get('mod_page_views', dict()).get(date, 0),
                                     'dailydls': stats.get('mod_daily_counts', dict()).get(date, 0),
                                     'time': date
                                    }
                            curs.execute(querydaily, data)

        queryfiles = 'INSERT INTO nexus_mod_files VALUES (%(gameid)s, %(modid)s, %(fileid)s, %(modversion)s, %(uploaded_time)s, %(filename)s, %(filesizekb)s) ON CONFLICT DO NOTHING;'
        queryfstats = 'INSERT INTO nexus_mod_files_stats VALUES (%(gameid)s, %(modid)s, %(fileid)s, %(category)s, %(dls)s, %(uniquedls)s, %(time)s);'
        with self.conn:
            with self.conn.cursor() as curs:
                for g,mods in self.files_stats.items():
                    for m,stats in mods.items():
                        for f,v in stats.items():
                            data = { 'gameid': self.crawler.gameid[g],
                                     'modid': m,
                                     'fileid': f,
                                     'modversion': v['version'],
                                     'uploaded_time': v['uploaded_time'],
                                     'filename': v['name'],
                                     'filesizekb': v['size_kb']
                                    }
                            curs.execute(queryfiles, data)

                            data = { 'gameid': self.crawler.gameid[g],
                                     'modid': m,
                                     'fileid': f,
                                     'category': v['category_name'],
                                     'dls': v['downloads'],
                                     'uniquedls': v['unique_downloads'],
                                     'time': self.t
                                    }
                            curs.execute(queryfstats, data)

if __name__ == '__main__':
    cfg = StatsConfig()
    try:
        conn = psycopg2.connect(cfg.getTimescaleDBString())

    except:
        print('Could not connect to database: check your connection info')
        exit()

    try:
        collector = TimescaleDBStatsCollector(cfg, conn)
        collector.collect()

        i = cfg.interval
        print(f'Starting update loop every {i} seconds')
        starttime=time()
        while True:
            sleep(i - ((time() - starttime) % i))
            print(f"{strftime('%c')}: polling stats update")
            collector.update()
            collector.collect()
    except Exception as e:
        print("error!")
        raise e
    finally:
        conn.commit()
        conn.close()
