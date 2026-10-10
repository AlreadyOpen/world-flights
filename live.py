"""Hong Kong near-live aircraft from the adsb.lol API (ODbL 1.0): one GET of /v2/point/22.3/114.2/250 (250 nm circle) per run.
Bucket (overwritten in place):  live/hk.json               the latest response as received, every field
                                live/hk-YYYY-MM-DD.parquet  that UTC day's snapshots so far, appended each run (GeoParquet: one row
                                                            per aircraft per snapshot, `aircraft` = the full API object as JSON)
On the first run of a UTC day, the previous day's file (now complete) is committed to the dataset, where it stays, and bucket
files older than KEEP_DAYS are removed from the bucket. On a 429 or any API error the run is skipped: no retry loop.
Needs HF_TOKEN. Usage: python3 live.py"""
import datetime, json, os, sys, tempfile, urllib.request
import duckdb
from huggingface_hub import HfApi, batch_bucket_files, download_bucket_files, list_bucket_tree

URL = 'https://api.adsb.lol/v2/point/22.3/114.2/250'
UA = {'User-Agent': 'AlreadyOpen world-flights (https://github.com/AlreadyOpen/world-flights)'}
REPO = 'alreadyopen/world-flights'
KEEP_DAYS = 30
ROWS = """
SELECT to_timestamp((j->>'now')::BIGINT / 1000) AS "snapshot", j->>'msg' AS "msg", (j->>'total')::INTEGER AS "total",
  (j->>'ctime')::BIGINT AS "ctime", (j->>'ptime')::BIGINT AS "ptime",
  a->>'hex' AS "hex", a->>'flight' AS "flight", a->>'r' AS "registration", a->>'t' AS "type", a->>'category' AS "category", a->>'type' AS "source",
  (a->>'lat')::DOUBLE AS "lat", (a->>'lon')::DOUBLE AS "lon",
  CASE WHEN a->>'alt_baro' = 'ground' THEN NULL ELSE (a->>'alt_baro')::INTEGER END AS "alt_baro", a->>'alt_baro' = 'ground' AS "on_ground",
  (a->>'alt_geom')::INTEGER AS "alt_geom", (a->>'gs')::DOUBLE AS "gs", (a->>'track')::DOUBLE AS "track", (a->>'seen_pos')::DOUBLE AS "seen_pos",
  (a->>'seen')::DOUBLE AS "seen", a AS "aircraft", ST_Point((a->>'lon')::DOUBLE, (a->>'lat')::DOUBLE) AS "geometry"
FROM (SELECT json j, unnest(json_extract(json, '$.ac[*]')) a FROM read_json_objects('{src}'))"""


def fetch():
    try:
        with urllib.request.urlopen(urllib.request.Request(URL, headers=UA), timeout=60) as r:
            body = r.read()
        d = json.loads(body)
        assert isinstance(d.get('ac'), list) and d.get('now'), f"unexpected response: {str(d)[:200]}"
        return body, d
    except Exception as e:                                             # 429, 5xx, timeout, bad JSON: back off until the next run
        print(f'::warning::adsb.lol API: {e}; skipping this run'); sys.exit(0)


def append(con, snap, old, out):
    """old (or None) + this snapshot -> out"""
    new = ROWS.format(src=snap)
    q = f"SELECT * FROM read_parquet('{old}') UNION ALL BY NAME {new}" if old else new
    con.execute(f"COPY ({q} ORDER BY snapshot, hex) TO '{out}' (FORMAT parquet, COMPRESSION zstd)")


def main():
    body, d = fetch()
    day = datetime.datetime.fromtimestamp(d['now'] / 1000, datetime.UTC).date()
    name = f'live/hk-{day}.parquet'
    w = tempfile.mkdtemp()
    snap, old, out = os.path.join(w, 'hk.json'), os.path.join(w, 'old.parquet'), os.path.join(w, 'new.parquet')
    open(snap, 'wb').write(body)
    on_bucket = {f.path for f in list_bucket_tree(REPO, prefix='live', recursive=True) if f.type == 'file'}
    if name in on_bucket: download_bucket_files(REPO, [(name, old)], raise_on_missing_files=True)
    con = duckdb.connect(); con.execute('INSTALL spatial; LOAD spatial')
    append(con, snap, old if name in on_bucket else None, out)
    rows = con.execute(f"SELECT count(*), count(DISTINCT snapshot) FROM '{out}'").fetchone()
    drop = []
    if name not in on_bucket:                                          # first run of a UTC day
        prev = f'live/hk-{day - datetime.timedelta(days=1)}.parquet'
        if prev in on_bucket:
            p = os.path.join(w, 'prev.parquet'); download_bucket_files(REPO, [(prev, p)], raise_on_missing_files=True)
            HfApi().upload_file(path_or_fileobj=p, path_in_repo=prev, repo_id=REPO, repo_type='dataset', commit_message=f'{prev}: complete day')
        cut = f'live/hk-{day - datetime.timedelta(days=KEEP_DAYS)}.parquet'
        drop = sorted(f for f in on_bucket if f.startswith('live/hk-') and f.endswith('.parquet') and f < cut)
    batch_bucket_files(REPO, add=[(snap, 'live/hk.json'), (out, name)], delete=drop or None)
    print(json.dumps({'snapshot': d['now'], 'aircraft': len(d['ac']), 'file': name, 'rows': rows[0], 'snapshots': rows[1], 'dropped': drop}))


if __name__ == '__main__':
    main()
