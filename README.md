# world-flights

An [AlreadyOpen](https://github.com/AlreadyOpen) pipeline: adsb.lol's daily global ADS-B history as GeoParquet (every point,
every field) plus a browser replay file, and Hong Kong near-live snapshots every 15 minutes. Published to the Hugging Face
dataset and bucket `alreadyopen/world-flights` (card: `hf/README.md`), mirrored to Kaggle `helenkwok/world-flights` (latest day
plus index). Data: adsb.lol contributors, ODbL 1.0.

| File | Does |
|---|---|
| `bake.py` | Latest `planes-readsb-prod-0` release of `adsblol/globe_history_<year>`: streams the split tar (curl into `tarfile`), one NDJSON batch of about 1 GB at a time into DuckDB (6 GB memory cap), writes `v/<D>/traces-NNN.parquet`, hourly `v/<D>/replay/HH.bin`, `v/<D>/acas.parquet` and the release's other files as delivered in `v/<D>/raw/`, then `index.json` (all days, read back from the bucket) and `latest.json`. `python3 bake.py <tag>` bakes another release, e.g. a small `...-mlatonly-0` for a local test |
| `publish.py` | The new day to the dataset (one commit) and the bucket; days older than the newest 30 leave the bucket only |
| `live.py`, `live.yml` | Every 15 minutes: one API call (250 nm around Hong Kong), `live/hk.json` and `live/hk-<UTC day>.parquet` on the bucket; a 429 or error skips the run |
| `bake.yml` | Daily at 04:30 UTC (adsb.lol publishes about 03:26 UTC); frees runner disk first |

Measured on 2026-10-09 data: the mlat-only release (42,187 aircraft, 10.1M points) bakes in 20 s locally; the first 300 MB of
the prod release held 7,847 aircraft and 10.6M points (442 MB Parquet). A full prod day is about 4.1 GB of tar, ~26 GB of JSON,
~150M points, ~6 GB of Parquet, ~1 GB of raw heatmap and ~0.7 GB of replay: about 8 GB a day (estimates scaled from that sample).

Built from [pipeline-template](https://github.com/AlreadyOpen/pipeline-template); `manifest.py`, `check.py`, `check.yml`
and `kaggle_mirror.py` are its shared files.

## Lessons (each cost a failed run once)

- Don't push to a pipeline repo while its run is going: the run's keep-alive push is rejected.
- Git keeps no empty folders: `mkdir -p` before writing into one.
- Linux has a smaller CA store than macOS: a server that leaves out an intermediate certificate fails only on the runner
  (hk-transit `mtr.py` bundles the missing one).
- Install DuckDB extensions once before any parallel work (`INSTALL` races on a fresh runner).
- An unquoted `: ` inside a workflow `run:` line makes the file invalid YAML, and GitHub silently drops its triggers
  ("does not have 'workflow_dispatch' trigger"). `check.py` now parses every workflow.
- Kaggle stores `.gz` files decompressed (`bus/10_10.json.gz` arrives as `bus/10_10.json`, at its full size), so the
  Kaggle copy's names and sha256 differ from `manifest.json`; say so in the card if the pipeline publishes `.gz`.
- `python publish.py | tee …` reports `tee`'s exit status, so a publish the gate refused showed as a green run. The publish
  step starts with `set -o pipefail` (found on hk-property, 2026-10-10).
- Never put client or private data in a pipeline repo: they are public, and so is their history.

Code: Apache-2.0. Data: under each source's own terms, listed in `sources.json`.
