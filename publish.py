"""Publish sources.OUT to Hugging Face (needs HF_TOKEN with write access to the alreadyopen org):
  dataset  REPO  DATASET_FILES + manifest.json + the card (hf/README.md): one commit a run, versioned (data tools)
  bucket   REPO  BUCKET_FILES + manifest.json, overwritten in place (read by browsers: CORS + HTTP Range)
Nothing is uploaded unless the publish gate passes (manifest.py). One file per source licence: never merge data under
different terms (e.g. ODbL share-alike with government open data) into one file.
Usage: python3 publish.py     (after bake.py)"""
import json, os
from huggingface_hub import HfApi, batch_bucket_files, create_bucket
import manifest, sources

REPO = 'alreadyopen/REPLACE-ME'
DATASET_FILES = ['index.json']                                         # e.g. the Parquet files
BUCKET_FILES = ['index.json']                                          # e.g. the PMTiles, JSON tiles
KAGGLE = ('helenkwok/REPLACE-ME', 'AlreadyOpen: REPLACE ME')            # mirrored by kaggle_mirror.py (title 6-50 chars)

def main():
    o = lambda f: os.path.join(sources.OUT, f); idx = json.load(open(o('index.json')))
    m = manifest.manifest(sources.OUT, sorted(set(DATASET_FILES + BUCKET_FILES)), idx['counts'], idx['built'])
    manifest.gate(m, f'https://huggingface.co/buckets/{REPO}/resolve/manifest.json')
    json.dump(m, open(o('manifest.json'), 'w'), indent=1)
    api = HfApi(); api.create_repo(REPO, repo_type='dataset', exist_ok=True)
    for f in DATASET_FILES + ['manifest.json']:
        api.upload_file(path_or_fileobj=o(f), path_in_repo=f, repo_id=REPO, repo_type='dataset', commit_message=f"{f}: bake of {idx['built']}")
    api.upload_file(path_or_fileobj=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hf', 'README.md'), path_in_repo='README.md', repo_id=REPO, repo_type='dataset', commit_message='card')
    create_bucket(REPO, private=False, exist_ok=True)
    batch_bucket_files(REPO, add=[(o(f), f) for f in BUCKET_FILES] + [(o('manifest.json'), 'manifest.json')])   # the gate reads the bucket's
    print(json.dumps({'dataset': f'https://huggingface.co/datasets/{REPO}', 'bucket': f'https://huggingface.co/buckets/{REPO}', 'built': idx['built'], 'counts': m['counts']}))

if __name__ == '__main__':
    main()
