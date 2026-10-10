---
pretty_name: World flights (adsb.lol ADS-B history and Hong Kong live)
license: odbl
license_name: odbl-1.0
license_link: https://opendatacommons.org/licenses/odbl/1-0/
tags:
  - geospatial
  - aviation
  - ads-b
  - geoparquet
---

# World flights

Every aircraft position adsb.lol's feeders received, one day at a time, plus near-live snapshots around Hong Kong. Rebuilt by
[AlreadyOpen/world-flights](https://github.com/AlreadyOpen/world-flights): the daily bake runs at 04:30 UTC, after adsb.lol
publishes the previous UTC day (about 03:26 UTC); the Hong Kong snapshot runs every 15 minutes.

## Files

- `v/<YYYY-MM-DD>/traces-NNN.parquet`: GeoParquet (`geometry` = POINT(lon lat), WGS 84), **one row per trace point, every
  point and every field** of adsb.lol's daily `globe_history` release (`planes-readsb-prod-0`). Split into parts of about a
  gigabyte of source JSON each; an aircraft is never split across parts. Columns:
  - per aircraft (repeated on each of its rows): `icao` (24-bit address, hex; `~` prefix = non-ICAO), `registration`, `type`
    (ICAO type code), `description`, `owner_operator`, `year`, `db_flags` (readsb bitfield: 1 military, 2 interesting, 4 PIA,
    8 LADD), `no_reg_data`, `readsb_version`, `day_start` (Unix seconds, 00:00 UTC of the day)
  - per point (readsb's trace array, in its order): `t` (seconds after `day_start`; `time` = the same as a timestamp), `lat`,
    `lon`, `altitude` (ft, barometric unless flag 8; NULL when on the ground or unknown), `on_ground`, `ground_speed` (kt),
    `track` (degrees; can be true heading when on the ground), `flags` (1 position stale, 2 start of a new leg, 4 vertical rate is
    geometric, 8 altitude is geometric), `vert_rate` (ft/min), `details` (readsb's full aircraft object as JSON, present when
    it changed: flight, squawk, category, nav_*, nic/nac/sil, wind, temperatures, ...), `source` (`adsb_icao`, `mlat`,
    `tisb_*`, `adsr_*`, ...), `alt_geom`, `geom_rate`, `ias`, `roll`
- `v/<YYYY-MM-DD>/replay.bin`: the same day for a map that replays it in a browser. **Downsampled: per aircraft, only the first
  position in each 30-second bucket is kept**, and only `t`, `lon`, `lat`, `altitude`, `ground_speed` and `track` (rounded:
  1e-5 degree, whole feet, whole knots, 0.1 degree). Everything else is in the Parquet, which is complete. Layout (no
  library needed: `DataView` and typed arrays): `AOR1`, a uint32 header length, a JSON header (`aircraft`:
  `[icao, registration, type, first point, count]` in icao order, `columns`, `layout`), then one little-endian column after
  another: `t` int32, `lon` int32, `lat` int32, `altitude` int32 (-999999 ground, -2147483648 unknown), `ground_speed` int16 and
  `track` int16 (-1 unknown). An aircraft's points are contiguous and time-ordered.
- `index.json`: every day baked, with aircraft and point counts, file names and URLs (dataset for all days; bucket while the day
  is among the newest 30). `latest.json`: the newest day.
- `live/hk-YYYY-MM-DD.parquet` (UTC day): GeoParquet, one row per aircraft per snapshot of the adsb.lol API within 250 nm of
  (22.3 N, 114.2 E), every 15 minutes; `aircraft` holds the full API object as JSON, with common fields as columns. On the bucket
  for 30 days; each complete day is also committed here. `live/hk.json` (bucket only): the latest response, as received.
- `manifest.json`: sha256 and size of the files of the latest daily bake, the counts and the sources.

The **bucket** (`huggingface.co/buckets/alreadyopen/world-flights`, CORS and HTTP Range) keeps the newest 30 days; this
**dataset** keeps every day (each bake is a commit) and nothing is deleted from it. The **Kaggle** copy
(`helenkwok/world-flights`) holds only the latest day plus `index.json`: one day is about 6 GB, so mirroring every day there
would not be sensible. Use `index.json` for older days.

## Source and licence

Data from [adsb.lol](https://adsb.lol) contributors ([historical data](https://www.adsb.lol/docs/open-data/historical/),
[GitHub releases](https://github.com/adsblol/globe_history_2026/releases), [API](https://api.adsb.lol/docs)), made available
under the [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/). Credit: "adsb.lol contributors,
ODbL 1.0". Feeders waive their rights to the raw data under CC0; adsb.lol releases the database under ODbL.

Every file here is a **derived database under the ODbL**: if you publicly use or share a database adapted from it, you must
release that adapted database under the ODbL (share-alike), credit adsb.lol contributors, and keep it open. That is why this
dataset holds adsb.lol data only and is kept apart from AlreadyOpen datasets under other licences; combining them is your
choice and your share-alike obligation. Aircraft registration and type fields come with readsb's database as bundled in the
release. Provided as is, with no warranty, and not endorsed by adsb.lol.
