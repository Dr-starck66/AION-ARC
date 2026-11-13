#!/usr/bin/env python3
"""ASTRA NFL 2027: bounded download and QC of four official small Kaggle CSVs.

Uses the existing Kaggle CLI OAuth under %%LOCALAPPDATA%%/ASTRA-Kaggle.
Zero GPU, kernels, submissions, dataset uploads, or external data exports.
The caller must have access to the competition dataset. Strict manifest checks
prevent a surprise multi-GB download. Request exact listed file paths.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from uuid import uuid4
import zipfile

COMPETITION = 'nfl-big-data-bowl-2027'
SMALL_FILES = {
    'combine_results.csv': 41020,
    'games.csv': 43174,
    'player_career_successes.csv': 13801,
    'players.csv': 47301,
}
HOME = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'ASTRA-Kaggle'
KAGGLE = HOME / '.venv' / 'Scripts' / 'kaggle.exe'
MAX_BYTES = 2_000_000
ALLOWED = {'files', 'download'}


def safe_error(s: str) -> str:
    s = re.sub(r'(?i)(token|password|authorization|secret|api_key)\s*[:=]\s*\S+', r'\1=[REDACTED]', s)
    return s[-800:]


def invoke(args: list[str], timeout: int = 120) -> tuple[int, str, str]:
    if len(args) < 2 or args[:1] != ['competitions'] or args[1] not in ALLOWED:
        raise ValueError('Forbidden Kaggle command')
    p = subprocess.run([str(KAGGLE), *args], capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=timeout, check=False)
    return p.returncode, p.stdout, safe_error(p.stderr)


def parse_official_listing(stdout: str) -> dict[str, int]:
    items: dict[str, int] = {}
    reader = csv.DictReader(stdout.splitlines())
    if not reader.fieldnames or not {'name', 'size'}.issubset(reader.fieldnames):
        raise ValueError('Unexpected competition files listing (no name/size)')
    for row in reader:
        full_name = (row.get('name') or '').strip()
        if not full_name.startswith(COMPETITION + '/'):
            continue
        filename = full_name[len(COMPETITION) + 1:]
        if filename not in SMALL_FILES:
            continue
        if filename in items:
            raise ValueError('Duplicate listed file: ' + filename)
        try:
            items[filename] = int(row.get('size', ''))
        except (ValueError, TypeError):
            raise ValueError('Invalid file size for ' + filename) from None
    if set(items) != set(SMALL_FILES):
        raise ValueError('Small-file manifest incomplete: ' + repr(sorted(items)))
    for filename, expected in SMALL_FILES.items():
        if items[filename] != expected:
            raise ValueError('Published size changed for ' + filename + ': '
                             + str(items[filename]) + ' != ' + str(expected))
    return items


def sha256_file(file: Path) -> str:
    h = hashlib.sha256()
    with file.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 128), b''):
            h.update(block)
    return h.hexdigest()


def _resolve_csv(download_dir: Path, filename: str) -> Path:
    paths = [p for p in download_dir.rglob(filename) if p.is_file() and not p.is_symlink()]
    if len(paths) == 1:
        return paths[0]
    if paths:
        raise ValueError('Duplicate local copies of ' + filename)
    # Kaggle may deliver an individual file as a ZIP; never unzip arbitrarily.
    zips = sorted(p for p in download_dir.rglob('*.zip') if p.is_file() and not p.is_symlink())
    if len(zips) != 1:
        raise ValueError('Expected one CSV or one ZIP for ' + filename)
    archive = zips[0]
    if archive.stat().st_size > MAX_BYTES:
        raise ValueError('ZIP larger than allowed')
    with zipfile.ZipFile(archive) as z:
        members = [m for m in z.infolist() if not m.is_dir()]
        if len(members) != 1:
            raise ValueError('ZIP must contain exactly one CSV')
        m = members[0]
        if (m.filename != filename and m.filename != COMPETITION + '/' + filename):
            raise ValueError('Unexpected ZIP member ' + m.filename)
        if m.file_size != SMALL_FILES[filename]:
            raise ValueError('ZIP member size mismatch')
        path = download_dir / filename
        with z.open(m) as src, path.open('xb') as dst:
            data = src.read(MAX_BYTES + 1)
            if len(data) != m.file_size:
                raise ValueError('ZIP content size mismatch')
            dst.write(data)
    return path


def inspect_csv(path: Path, filename: str) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ValueError('Missing or symlink file: ' + filename)
    size = path.stat().st_size
    if size != SMALL_FILES[filename]:
        raise ValueError('Downloaded file size mismatch: ' + filename)
    with path.open('r', encoding='utf-8-sig', errors='strict', newline='') as f:
        rd = csv.reader(f, strict=True)
        head = next(rd, None)
        if not head or any(not col.strip() for col in head) or len(set(head)) != len(head):
            raise ValueError('Invalid columns: ' + filename)
        nrows = 0
        for row in rd:
            if len(row) != len(head):
                raise ValueError('Inconsistent CSV width: ' + filename)
            nrows += 1
        if nrows == 0:
            raise ValueError('CSV without data rows: ' + filename)
    return {'filename': filename, 'bytes': size, 'rows': nrows,
            'columns': head, 'sha256': sha256_file(path)}


def download_small_files(dest: Path) -> list[dict]:
    code, listing, stderr = invoke(['competitions', 'files', COMPETITION,
                                    '--page-size', '20', '-v'], timeout=90)
    if code:
        raise RuntimeError('Official competition listing failed: ' + (stderr or safe_error(listing)))
    parse_official_listing(listing)
    results = []
    for filename in SMALL_FILES:
        subdir = dest / 'files' / filename.removesuffix('.csv')
        subdir.mkdir(parents=True, exist_ok=False)
        code, output, err = invoke(['competitions', 'download', COMPETITION,
                                    '-f', COMPETITION + '/' + filename, '-p', str(subdir)], timeout=150)
        if code:
            raise RuntimeError('Download failed for listed path ' + COMPETITION + '/' + filename + ': ' + (err or safe_error(output)) + '; possible rights/rules restriction or Kaggle API path issue; no bulk fallback')
        result = inspect_csv(_resolve_csv(subdir, filename), filename)
        results.append(result)
        print('ASTRA_NFL_OFFICIAL_FILE_PASS ' + filename + ' rows=' + str(result['rows'])
              + ' sha256=' + result['sha256'], flush=True)
    return results


def main() -> int:
    if not KAGGLE.is_file():
        print('ASTRA_NFL_FAIL Kaggle CLI missing at the existing local path', flush=True)
        return 2
    dest = HOME / 'research' / 'nfl' / ('small-csv-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
                                      + '-' + uuid4().hex[:8])
    dest.mkdir(parents=True, exist_ok=False)
    receipt = {'kind': 'astra_nfl_official_small_csv_preflight_v1',
               'competition': COMPETITION,
               'source': 'https://www.kaggle.com/competitions/' + COMPETITION,
               'timestamp_utc': datetime.now(timezone.utc).isoformat(),
               'manifest_expected_bytes': SMALL_FILES,
               'status': 'UNVERIFIED', 'science': 'UNVERIFIED',
               'join_analysis': 'UNVERIFIED', 'prediction': 'UNVERIFIED',
               'no_kernel_push': True, 'no_gpu': True, 'no_submission': True,
               'local_report_path': str(dest / 'report.json')}
    try:
        items = download_small_files(dest)
        receipt.update({'status': 'PARTIAL', 'gate': 'OFFICIAL_SMALL_CSV_QC_PASS',
                        'files': items, 'files_count': len(items),
                        'total_bytes': sum(f['bytes'] for f in items)})
        print('ASTRA_NFL_DATA_PARTIAL gate=OFFICIAL_SMALL_CSV_QC_PASS count=4', flush=True)
        return 0
    except Exception as exc:
        receipt.update({'status': 'FAIL', 'gate': 'OFFICIAL_SMALL_CSV_QC_FAILED',
                        'error_type': type(exc).__name__, 'error': safe_error(str(exc))})
        print('ASTRA_NFL_DATA_FAIL ' + type(exc).__name__ + ': '
              + receipt['error'], flush=True)
        return 1
    finally:
        (dest / 'report.json').write_text(json.dumps(receipt, indent=2, ensure_ascii=False)
                                         + '\n', encoding='utf-8')
        print('ASTRA_NFL_REPORT ' + str(dest / 'report.json'), flush=True)
        print('NO_GPU NO_KERNEL_PUSH NO_COMPETITION_SUBMISSION', flush=True)

if __name__ == '__main__':
    sys.exit(main())
