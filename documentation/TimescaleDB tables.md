# TimescaleDB tables

These tables are automatically created by running `./timescaledb_exporter.py`:

## games
```
                         Table "public.games"
 Column |  Type   | Modifiers | Storage  | Stats target | Description
--------+---------+-----------+----------+--------------+-------------
 gameid | integer | not null  | plain    |              |
 game   | text    | not null  | extended |              |
Indexes:
    "games_pkey" PRIMARY KEY, btree (gameid)
    "games_game_key" UNIQUE CONSTRAINT, btree (game)
```

## mods

```
                            Table "public.mods"
   Column    |  Type   | Modifiers | Storage  | Stats target | Description
-------------+---------+-----------+----------+--------------+-------------
 gameid      | integer | not null  | plain    |              |
 modid       | integer | not null  | plain    |              |
 mod         | text    | not null  | extended |              |
 picture_url | text    |           | extended |              |
Indexes:
    "mods_pkey" PRIMARY KEY, btree (gameid, modid)
Foreign-key constraints:
    "mods_gameid_fkey" FOREIGN KEY (gameid) REFERENCES games(gameid) ON DELETE RESTRICT
```

## endorsements

```
                                Table "public.endorsements"
    Column    |           Type           | Modifiers | Storage | Stats target | Description
--------------+--------------------------+-----------+---------+--------------+-------------
 gameid       | integer                  | not null  | plain   |              |
 modid        | integer                  | not null  | plain   |              |
 endorsements | integer                  | not null  | plain   |              |
 time         | timestamp with time zone | not null  | plain   |              |
Indexes:
    "endorsements_pkey" PRIMARY KEY, btree (gameid, modid, "time")
    "endorsements_time_idx" btree ("time" DESC)
Foreign-key constraints:
    "endorsements_gameid_fkey" FOREIGN KEY (gameid) REFERENCES games(gameid) ON DELETE RESTRICT
    "endorsements_gameid_fkey1" FOREIGN KEY (gameid, modid) REFERENCES mods(gameid, modid) ON DELETE RESTRICT
```

## nexus_mod_files

```
                                Table "public.nexus_mod_files"
    Column     |           Type           | Modifiers | Storage  | Stats target | Description
---------------+--------------------------+-----------+----------+--------------+-------------
 gameid        | integer                  | not null  | plain    |              |
 modid         | integer                  | not null  | plain    |              |
 fileid        | integer                  | not null  | plain    |              |
 modversion    | text                     | not null  | extended |              |
 uploaded_time | timestamp with time zone | not null  | plain    |              |
 filename      | text                     | not null  | extended |              |
 filesizekb    | integer                  | not null  | plain    |              |
Indexes:
    "nexus_mod_files_pkey" PRIMARY KEY, btree (gameid, modid, fileid)
Foreign-key constraints:
    "nexus_mod_files_gameid_fkey" FOREIGN KEY (gameid) REFERENCES games(gameid) ON DELETE RESTRICT
    "nexus_mod_files_gameid_fkey1" FOREIGN KEY (gameid, modid) REFERENCES mods(gameid, modid) ON DELETE RESTRICT
```

## nexus_mod_files_stats

```
                           Table "public.nexus_mod_files_stats"
  Column   |           Type           | Modifiers | Storage  | Stats target | Description
-----------+--------------------------+-----------+----------+--------------+-------------
 gameid    | integer                  | not null  | plain    |              |
 modid     | integer                  | not null  | plain    |              |
 fileid    | integer                  | not null  | plain    |              |
 category  | text                     | not null  | extended |              |
 dls       | integer                  | not null  | plain    |              |
 uniquedls | integer                  | not null  | plain    |              |
 time      | timestamp with time zone | not null  | plain    |              |
Indexes:
    "nexus_mod_files_stats_pkey" PRIMARY KEY, btree (gameid, modid, fileid, "time")
    "nexus_mod_files_stats_time_idx" btree ("time" DESC)
Foreign-key constraints:
    "nexus_mod_files_stats_gameid_fkey" FOREIGN KEY (gameid) REFERENCES games(gameid) ON DELETE RESTRICT
    "nexus_mod_files_stats_gameid_fkey1" FOREIGN KEY (gameid, modid) REFERENCES mods(gameid, modid) ON DELETE RESTRICT
    "nexus_mod_files_stats_gameid_fkey2" FOREIGN KEY (gameid, modid, fileid) REFERENCES nexus_mod_files(gameid, modid, fileid) ON DELETE RESTRICT
```

## nexus_mod_stats_daily

```
                  Table "public.nexus_mod_stats_daily"
  Column   |  Type   | Modifiers | Storage | Stats target | Description
-----------+---------+-----------+---------+--------------+-------------
 gameid    | integer | not null  | plain   |              |
 modid     | integer | not null  | plain   |              |
 pageviews | integer | not null  | plain   |              |
 dailydls  | integer | not null  | plain   |              |
 time      | date    | not null  | plain   |              |
Indexes:
    "nexus_mod_stats_daily_pkey" PRIMARY KEY, btree (gameid, modid, "time")
    "nexus_mod_stats_daily_time_idx" btree ("time" DESC)
Foreign-key constraints:
    "nexus_mod_stats_daily_gameid_fkey" FOREIGN KEY (gameid) REFERENCES games(gameid) ON DELETE RESTRICT
    "nexus_mod_stats_daily_gameid_fkey1" FOREIGN KEY (gameid, modid) REFERENCES mods(gameid, modid) ON DELETE RESTRICT
```

## nexus_mod_stats_total

```
                          Table "public.nexus_mod_stats_total"
  Column  |           Type           | Modifiers | Storage | Stats target | Description
----------+--------------------------+-----------+---------+--------------+-------------
 gameid   | integer                  | not null  | plain   |              |
 modid    | integer                  | not null  | plain   |              |
 totaldls | integer                  | not null  | plain   |              |
 time     | timestamp with time zone | not null  | plain   |              |
Indexes:
    "nexus_mod_stats_total_pkey" PRIMARY KEY, btree (gameid, modid, "time")
    "nexus_mod_stats_total_time_idx" btree ("time" DESC)
Foreign-key constraints:
    "nexus_mod_stats_total_gameid_fkey" FOREIGN KEY (gameid) REFERENCES games(gameid) ON DELETE RESTRICT
    "nexus_mod_stats_total_gameid_fkey1" FOREIGN KEY (gameid, modid) REFERENCES mods(gameid, modid) ON DELETE RESTRICT
```