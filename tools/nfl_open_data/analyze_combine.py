#!/usr/bin/env python3
"""ASTRA independent NFL Combine dataset audit; no Kaggle, no competition.

Input is a publicly readable git-hosted CSV; Git-blob SHA-1 pins the content.
Run with: python analyze_combine.py --input path/to/combine_official.csv
Or omit --input to retrieve the pinned public CSV by HTTPS. Does not upload data.
No prediction, betting recommendation, training or contest submission.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import statistics
from urllib.request import urlopen

SOURCE = 'https://raw.githubusercontent.com/array-carpenter/nfl-draft-data/master/data/combine_official.csv'
EXPECTED_GIT_BLOB = 'dcc6532ba88038cad3d9f974ea7654b2a6e5988a'
MAX_BYTES = 3_000_000
REQUIRED = {'year', 'player', 'person_id', 'position_group', 'forty_yard_dash', 'vertical_jump'}


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def load_data(path: str | None):
    if path:
        p = Path(path)
        if p.is_symlink() or not p.is_file() or p.stat().st_size > MAX_BYTES:
            raise ValueError('Local CSV missing, symlink or oversized')
        raw = p.read_bytes()
    else:
        with urlopen(SOURCE, timeout=45) as r:
            raw = r.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('File exceeds 3 MB safety limit')
    if git_blob_sha1(raw) != EXPECTED_GIT_BLOB:
        raise ValueError('Source Git blob changed; refused to compare different snapshots')
    return raw


def valid_number(value: str, low: float, high: float):
    if not value:
        return None
    try:
        f = float(value)
    except ValueError:
        return None
    return f if low < f < high else None


def analyze(raw: bytes, source_blob: str | None = None) -> dict:
    with io.StringIO(raw.decode('utf-8-sig'), newline='') as data:
        reader = csv.DictReader(data, strict=True)
        if reader.fieldnames is None or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError('Missing or duplicate column names')
        if not REQUIRED.issubset(reader.fieldnames):
            raise ValueError('Missing required columns')
        by_position: dict[str, dict] = {}
        by_year: dict[str, int] = {}
        seen: set[tuple[str, str]] = set()
        count = duplicates = unclassified = measured40 = measured_vj = both = 0
        for row in reader:
            if None in row:  # ragged CSV; csv.DictReader keys overflow as None
                raise ValueError('CSV row has extra fields')
            if any(value is None for value in row.values()):
                raise ValueError('CSV row has missing fields')
            count += 1
            year = (row['year'] or '').strip()
            if not year.isdecimal() or not (2000 <= int(year) <= 2030):
                raise ValueError('Unexpected year')
            by_year[year] = by_year.get(year, 0) + 1
            if not row['player'].strip():
                raise ValueError('Unnamed player')
            pid = row['person_id'].strip()
            if pid:
                key = (year, pid)
                if key in seen:
                    duplicates += 1
                seen.add(key)
            position = row['position_group'].strip() or 'UNCLASSIFIED'
            unclassified += position == 'UNCLASSIFIED'
            item = by_position.setdefault(position, {'rows': 0, 'dashes': [], 'verticals': []})
            item['rows'] += 1
            dash = valid_number(row['forty_yard_dash'], 3, 8)
            vert = valid_number(row['vertical_jump'], 10, 55)
            if dash is not None:
                item['dashes'].append(dash)
                measured40 += 1
            if vert is not None:
                item['verticals'].append(vert)
                measured_vj += 1
            if dash is not None and vert is not None:
                both += 1
    groups = []
    for pos, item in sorted(by_position.items(), key=lambda pair: (-pair[1]['rows'], pair[0])):
        groups.append({'group': pos, 'rows': item['rows'],
                       'forty_n': len(item['dashes']),
                       'forty_median_seconds': statistics.median(item['dashes']) if item['dashes'] else None,
                       'vertical_n': len(item['verticals']),
                       'vertical_median_inches': statistics.median(item['verticals']) if item['verticals'] else None})
    return {'source_url': SOURCE, 'source_git_blob_sha1': source_blob or git_blob_sha1(raw),
            'row_count': count, 'column_count': len(reader.fieldnames),
            'year_counts': dict(sorted(by_year.items())), 'duplicate_player_year': duplicates,
            'unclassified_position': unclassified, 'valid_40': measured40,
            'valid_vertical': measured_vj, 'valid_both': both,
            'position_groups': groups, 'statistical_prediction': 'UNVERIFIED',
            'competition': 'NOT_USED', 'scientific_validation': 'UNVERIFIED'}


def main():
    p = argparse.ArgumentParser(description='Offline/public NFL Combine descriptive audit')
    p.add_argument('--input', help='existing source CSV; default downloads public fixed-blob source')
    p.add_argument('--output', help='local JSON report (optional)')
    ns = p.parse_args()
    raw = load_data(ns.input)
    obj = analyze(raw, git_blob_sha1(raw))
    report = json.dumps(obj, indent=2, sort_keys=True) + '\n'
    if ns.output:
        Path(ns.output).write_text(report, encoding='utf-8')
    print('ASTRA_NFL_OPEN_QC_PASS rows=' + str(obj['row_count']) + ' blob=' + obj['source_git_blob_sha1'])
    print(report)

if __name__ == '__main__':
    main()
