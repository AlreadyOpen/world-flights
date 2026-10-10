"""Publish the new day from sources.OUT to Hugging Face (needs HF_TOKEN with write access to the alreadyopen org):
  dataset  REPO  the day's files (v/<D>/...), index.json, latest.json, manifest.json and the card, in one commit; every day stays
                 there (versioned), nothing is deleted
  bucket   REPO  the same files, overwritten in place (read by browsers: CORS + HTTP Range); days older than the newest 30 are
                 removed from the bucket only (index.json `bucket_drop`)
Nothing is uploaded unless the publish gate passes (manifest.py). The gate counts are totals over every day in the index, so a
quiet weekend day never trips it; bake.py stops a day with under half the previous day's points. The manifest lists this bake's
files: earlier days' files are not "gone", so the gate compares only the files outside v/.
Usage: python3 publish.py     (after bake.py)"""
import json, os, sys
from huggingface_hub import CommitOperationAdd, HfApi, batch_bucket_files, create_bucket
import bake, manifest, sources

REPO = bake.REPO
_idx = os.path.join(sources.OUT, 'index.json')
NEW = json.load(open(_idx)).get('new', []) if os.path.exists(_idx) else []
DATASET_FILES = ['index.json', 'latest.json'] + NEW
BUCKET_FILES = DATASET_FILES
KAGGLE = ('helenkwok/world-flights', 'AlreadyOpen: World flights (adsb.lol)')   # latest day + index (title 6-50 chars)


def main():
    o = lambda f: os.path.join(sources.OUT, f); idx = json.load(open(o('index.json')))
    if not NEW:
        print(json.dumps({'nothing new': True, 'days': idx['counts']['days'] if 'counts' in idx else 0})); return
    m = manifest.manifest(sources.OUT, sorted(set(DATASET_FILES + BUCKET_FILES)), idx['counts'], idx['built'])
    old = manifest.published(f'https://huggingface.co/buckets/{REPO}/resolve/manifest.json')
    if old: old['files'] = {f: v for f, v in old['files'].items() if not f.startswith('v/')}
    p = manifest.problems(m, old)
    if p and os.environ.get('PUBLISH_FORCE') != '1':
        sys.exit('publish gate: not publishing (PUBLISH_FORCE=1 overrides):\n  ' + '\n  '.join(p))
    for x in p: print(f'publish gate: forced past: {x}', file=sys.stderr)
    json.dump(m, open(o('manifest.json'), 'w'), indent=1)
    api = HfApi(); api.create_repo(REPO, repo_type='dataset', exist_ok=True)
    card = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hf', 'README.md')
    api.create_commit(REPO, repo_type='dataset', commit_message=f"{idx['days'][-1]['day']}: bake of {idx['built']}",
                      operations=[CommitOperationAdd(f, o(f)) for f in DATASET_FILES + ['manifest.json']] + [CommitOperationAdd('README.md', card)])
    create_bucket(REPO, private=False, exist_ok=True)
    batch_bucket_files(REPO, add=[(o(f), f) for f in BUCKET_FILES] + [(o('manifest.json'), 'manifest.json')],
                       delete=idx.get('bucket_drop') or None)                         # the gate reads the bucket's manifest
    print(json.dumps({'dataset': f'https://huggingface.co/datasets/{REPO}', 'bucket': f'https://huggingface.co/buckets/{REPO}',
                      'built': idx['built'], 'day': idx['days'][-1]['day'], 'counts': m['counts'], 'bucket_drop': len(idx.get('bucket_drop', []))}))


if __name__ == '__main__':
    main()
