"""Export the four original R data frames, retaining every original column."""
import hashlib
import json
import shutil
import urllib.request
import warnings
import pandas as pd
import rdata
from common import ROOT

COMMIT = 'c38586571a6f0d3cc3f42ebb457410020eb8898b'
BASE = f'https://raw.githubusercontent.com/bozhinvi/volleystat/{COMMIT}/'

def main():
    raw = ROOT / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    manifest = {'repository': 'https://github.com/bozhinvi/volleystat',
                'commit': COMMIT, 'license_declared_in_DESCRIPTION': 'CC0', 'files': {}}
    for name in ['players', 'matches', 'sets', 'matchstats']:
        target = raw / f'{name}.rda'
        url = BASE + f'data/{name}.rda'
        if not target.exists():
            with urllib.request.urlopen(url, timeout=90) as response, target.open('wb') as out:
                shutil.copyfileobj(response, out)
        # rdata returns R Date as days and POSIXct as seconds since the Unix epoch.
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            df = rdata.read_rda(target)[name]
        if name == 'players':
            df['birthdate'] = pd.to_datetime(df.birthdate, unit='D', origin='unix').dt.strftime('%Y-%m-%d')
        if name == 'matches':
            df['date_time'] = pd.to_datetime(df.date_time, unit='s', utc=True).dt.tz_convert('Europe/Berlin').dt.strftime('%Y-%m-%d %H:%M:%S')
        df.to_csv(raw / f'{name}.csv', index=False, encoding='utf-8')
        manifest['files'][name] = {'url': url, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                                  'rows': len(df), 'columns': list(df.columns)}
        print(f'{name}: {len(df):,} rows exported')
    for path in ['README.md', 'DESCRIPTION', 'R/data.R']:
        with urllib.request.urlopen(BASE + path, timeout=60) as response:
            (raw / ('source_' + path.replace('/', '_'))).write_bytes(response.read())
    (raw / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')

if __name__ == '__main__':
    main()
