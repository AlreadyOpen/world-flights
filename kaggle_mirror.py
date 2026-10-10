"""Mirror what publish.py published to a public Kaggle dataset (the same file in every AlreadyOpen pipeline).
Kaggle's "Remote URL" cannot pull from Hugging Face (every HF download is a 302 to a signed URL, which Kaggle refuses; a direct
200 URL is accepted), so the files are uploaded. Runs after publish.py as its own step with continue-on-error: Kaggle failing
never blocks Hugging Face. Needs KAGGLE_API_TOKEN in the environment (a repo secret; never on argv). The dataset is owned by
Helen's account (helenkwok): a Kaggle group cannot own one. Description = hf/README.md without its YAML header; licence "other"
(per-file terms are in the description).
By default it mirrors EVERYTHING publish.py publishes (DATASET_FILES + BUCKET_FILES + manifest.json), keeping relative paths;
a folder is uploaded as a zip that Kaggle unpacks again (Kaggle allows only 50 top-level files). Mirroring less is a narrowing:
ask Helen first.
Usage: python3 kaggle_mirror.py                                  (reads REPO, DATASET_FILES, BUCKET_FILES, KAGGLE from publish.py)
       python3 kaggle_mirror.py <owner/slug> "<title>" <root> <path>...  (paths relative to root)"""
import json, os, re, subprocess, sys, tempfile

def card_body():
    t = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hf', 'README.md'), encoding='utf-8').read()
    return re.sub(r'\A---\n.*?\n---\n', '', t, flags=re.S).strip()

def mirror(slug, title, root, paths):
    exists = subprocess.run(['kaggle', 'datasets', 'files', slug], capture_output=True).returncode == 0
    with tempfile.TemporaryDirectory() as d:
        for p in paths:                                                    # keep relative paths: bus/x.json.gz -> bus/...
            dst = os.path.join(d, p.split('/')[0])
            if not os.path.exists(dst):
                os.symlink(os.path.abspath(os.path.join(root, p.split('/')[0])), dst)
        meta = {'title': title, 'id': slug, 'licenses': [{'name': 'other'}], 'description': card_body()}
        json.dump(meta, open(os.path.join(d, 'dataset-metadata.json'), 'w'), indent=1)
        mode = ['-r', 'zip']                                               # folders go up zipped; Kaggle unpacks them
        if exists:
            cmd = ['kaggle', 'datasets', 'version', '-p', d, '-m', os.environ.get('KAGGLE_MESSAGE', 'update'), '-t', '-q', *mode]
        else:
            cmd = ['kaggle', 'datasets', 'create', '-p', d, '--public', '-t', '-q', *mode]
        subprocess.run(cmd, check=True)
    print(json.dumps({'kaggle': f'https://www.kaggle.com/datasets/{slug}', 'paths': sorted({p.split('/')[0] for p in paths}),
                      'versioned' if exists else 'created': True}))

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if len(sys.argv) < 5:
            sys.exit(__doc__)
        mirror(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])
    else:
        import publish, sources
        mirror(*publish.KAGGLE, sources.OUT, sorted(set(publish.DATASET_FILES + publish.BUCKET_FILES + ['manifest.json'])))
