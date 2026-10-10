"""Replace with the pipeline's bake. Contract with publish.py: write every output into sources.OUT, plus index.json with
  built: ISO time of the bake
  counts: {name: int} the publish gate compares with the last published manifest (a drop > 10% stops the publish)
Download into sources.CACHE (kept between runs by the workflow), and reuse a download when its content is unchanged.
Usage: python3 bake.py"""
import datetime, json, os
import sources

def main():
    os.makedirs(sources.OUT, exist_ok=True)
    raise NotImplementedError('write the outputs into sources.OUT, then the index below')
    rows = []
    idx = {'built': datetime.datetime.now().isoformat(timespec='seconds'), 'counts': {'rows': len(rows)}}
    json.dump(idx, open(os.path.join(sources.OUT, 'index.json'), 'w'), indent=1)

if __name__ == '__main__':
    main()
