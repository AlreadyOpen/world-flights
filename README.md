# pipeline-template

The starting point for an [AlreadyOpen](https://github.com/AlreadyOpen) pipeline: a GitHub Action that bakes public data and
publishes it to a Hugging Face dataset (versioned, for data tools) and bucket (overwritten in place, read by browsers with CORS
and HTTP Range). Used by hk-transit, hk-buildings and world-skylines; `manifest.py`, `check.py` and `check.yml` are identical in
all of them, so fix them here and copy them out.

## Start a pipeline

1. **Use this template** on GitHub, name the repo after its data (e.g. `hk-parking`).
2. `sources.json`: every source with its owner, URL, licence link and the script that reads it.
3. `bake.py`: write the outputs into `data/out/` and `index.json` with `built` and `counts`.
4. `publish.py`: set `REPO`, `DATASET_FILES` and `BUCKET_FILES`. One file per source licence: never merge data under different
   terms into one file.
5. `hf/README.md`: the dataset card, crediting every owner in `sources.json` (`check.py` fails otherwise).
6. `publish.py`: set `KAGGLE` (`helenkwok/<repo>` and a 6-50 character title). The Kaggle mirror takes everything published.
7. `python check.py`, then set both secrets from their files (never echo a token):
   `gh secret set HF_TOKEN -R AlreadyOpen/<repo> < "$HOME/Library/Application Support/alreadyopen/hf-write.key"` and
   `gh secret set KAGGLE_API_TOKEN -R AlreadyOpen/<repo> < "$HOME/.kaggle/access_token"`. Add a schedule to
   `.github/workflows/bake.yml` and run it once by hand.

## What comes with it

| File | Does |
|---|---|
| `manifest.py` | `manifest.json`: sha256 and size of every published file, the counts, the sources. The publish gate refuses (before any upload) when a count drops > 10%, a count or file disappears, or a file is empty; a manual run's **force** box overrides it |
| `check.py`, `check.yml` | On every push, no data and no token: scripts compile, `sources.json` is complete, the card credits every owner and has `license_link`, the gate's self-test passes |
| `kaggle_mirror.py` | After publish, uploads everything published to a public Kaggle dataset (`helenkwok/<repo>`), keeping folders (zipped, Kaggle unpacks them). Own step, allowed to fail. Kaggle cannot pull from Hugging Face itself: its Remote URL refuses HF's 302 redirects |
| `bake.yml` | Pinned action SHAs; the download cache saved even when publish fails; a keep-alive commit (schedules stop after 60 days without commits) rebased before pushing |

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
