# SQL Queries

Some examplary SQL Queries you could use with Grafana. See also `timescaledb_dashboard_example.json`.

## Unique Downloads Count per Main File of Game mygame, Mod 123

```
SELECT
  $__timeGroupAlias("time",$__interval),
  CONCAT(modversion, ' ', filename) AS metric,
  avg(uniquedls) AS "uniquedls"
FROM nexus_mod_files_stats AS s
INNER JOIN nexus_mod_files AS f
  ON (s.gameid = f.gameid AND s.modid = f.modid AND s.fileid = f.fileid)
INNER JOIN mods AS m
  ON (s.gameid = m.gameid AND s.modid = m.modid)
INNER JOIN games AS g
  ON (s.gameid = g.gameid)
WHERE
  game = 'mygame' AND
  m.modid = 123 AND
  $__timeFilter("time") AND
  category = 'MAIN'
GROUP BY 1,2,modversion,category
ORDER BY modversion DESC, category ASC, time ASC;
```

## Downloads per View relative to Average Downloads per View

```
SELECT
  $__timeGroup("time",$__interval),
  mod AS metric,
  (rate/total) - 1 AS rrate
FROM (
  SELECT
    d.gameid,
    d.modid,
    d.time,
    (CAST(dailydls AS FLOAT) / CAST(pageviews AS FLOAT)) AS rate
  FROM nexus_mod_stats_daily AS d
  ) AS d
INNER JOIN (
  SELECT
    d.gameid,
    d.modid,
    game,
    CAST(SUM(dailydls) AS FLOAT) / CAST(SUM(pageviews) AS FLOAT) AS total
  FROM nexus_mod_stats_daily AS d
  INNER JOIN games AS g
    ON (d.gameid = g.gameid)
  WHERE
    CONCAT(d.gameid,' ',d.modid) IN ($modid)
  GROUP BY d.gameid,modid,game
  ) AS t
  ON (d.gameid = t.gameid AND d.modid = t.modid)
INNER JOIN mods AS m
  ON (d.gameid = m.gameid AND d.modid = m.modid)
WHERE
  $__timeFilter("time")
ORDER BY game, time ASC
```