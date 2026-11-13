#!/usr/bin/env python3
"""ASTRA NFL OPEN CAREER Ω — no contests, no Kaggle or GPU.

Independent public nflverse combine + draft_picks tables joined *only* by
(pfr player id, draft/combine season). Career games >= 50 is a mature-cohort
milestone, not a within-3-year outcome; no player-level uploads.

Holdout: train draft classes 2006-2013; select C on 2014-2015 validation;
refit on train+validation, evaluate 2016-2018 exactly once.

Does NOT infer career failure from unmatched Combine players or null career games.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

COMBINE_URL = 'https://github.com/nflverse/nflverse-data/releases/download/combine/combine.csv'
DRAFT_URL = 'https://github.com/nflverse/nflverse-data/releases/download/draft_picks/draft_picks.csv'
LIMIT_BYTES = 16_000_000
SOURCE_COLS = ('season', 'player_pfr_id', 'pos', 'forty', 'vertical', 'bench', 'broad_jump', 'cone', 'shuttle')
DRAFT_COLS = ('season', 'player_pfr_id', 'pick', 'games')
ATHLETIC_COLS = ('forty', 'vertical', 'bench', 'broad_jump', 'cone', 'shuttle')
SPLITS = {'train': (2006, 2013), 'validation': (2014, 2015), 'test': (2016, 2018)}


def load_blob(url: str, local_file: str | None = None) -> tuple[bytes, str]:
    if local_file:
        p = Path(local_file)
        if p.is_symlink() or not p.is_file() or p.stat().st_size > LIMIT_BYTES:
            raise ValueError('Local source is absent, symlinked, or too large')
        data = p.read_bytes()
    else:
        with urlopen(Request(url, headers={'User-Agent': 'ASTRA-NFL-public-research/1.0'}), timeout=35) as resp:
            data = resp.read(LIMIT_BYTES + 1)
    if not data or len(data) > LIMIT_BYTES:
        raise ValueError('Source empty or > 16 MB safety limit')
    return data, hashlib.sha256(data).hexdigest()


def read_csv(raw: bytes, required: tuple[str, ...], source: str) -> pd.DataFrame:
    text = raw.decode('utf-8-sig', errors='strict')
    header = next(csv.reader(io.StringIO(text)), None)
    if not header or len(header) != len(set(header)) or not set(required).issubset(header):
        raise ValueError(f'{source}: invalid/duplicate/missing required CSV columns')
    frame = pd.read_csv(io.StringIO(text), dtype={'player_pfr_id': 'string'}, low_memory=False)
    if frame.empty:
        raise ValueError(f'{source}: no rows')
    return frame.loc[:, list(required)].copy()


def prepare(combine: pd.DataFrame, draft: pd.DataFrame):
    """Fail closed on any duplicated join key. Do not fuzzy-match players."""
    audit = {'combine_rows': len(combine), 'draft_rows': len(draft)}
    for label, frame in [('combine', combine), ('draft', draft)]:
        frame['season'] = pd.to_numeric(frame['season'], errors='coerce')
        frame['player_pfr_id'] = frame['player_pfr_id'].astype('string').str.strip()
        frame.dropna(subset=['season', 'player_pfr_id'], inplace=True)
        frame.drop(frame[frame['player_pfr_id'].eq('')].index, inplace=True)
        frame['season'] = frame['season'].astype('int64')
        dup = int(frame.duplicated(['season', 'player_pfr_id'], keep=False).sum())
        audit[label + '_duplicate_keys'] = dup
        if dup:
            raise ValueError(f'{label}: {dup} duplicate join keys; refusing ambiguous join')
    combine['pos'] = combine['pos'].astype('string').str.upper().str.strip().fillna('UNKNOWN')
    for col in ATHLETIC_COLS:
        combine[col] = pd.to_numeric(combine[col], errors='coerce')
    combine.loc[~combine['forty'].between(3.1, 7.5), 'forty'] = np.nan
    combine.loc[~combine['vertical'].between(15, 50), 'vertical'] = np.nan
    combine.loc[~combine['bench'].between(0, 65), 'bench'] = np.nan
    combine.loc[~combine['broad_jump'].between(60, 160), 'broad_jump'] = np.nan
    combine.loc[~combine['cone'].between(5, 11), 'cone'] = np.nan
    combine.loc[~combine['shuttle'].between(3, 7), 'shuttle'] = np.nan
    draft['pick'] = pd.to_numeric(draft['pick'], errors='coerce')
    draft['games'] = pd.to_numeric(draft['games'], errors='coerce')
    merged = combine.merge(draft, on=['season', 'player_pfr_id'], how='left', validate='one_to_one', indicator=True)
    audit['unmatched_combine_count'] = int(merged['_merge'].eq('left_only').sum())
    audit['matched_combine_count'] = int(merged['_merge'].eq('both').sum())
    merged = merged[merged['_merge'].eq('both')].drop(columns=['_merge'])
    null_games = int(merged['games'].isna().sum())
    audit['matched_null_career_games'] = null_games
    audit['matched_negative_career_games'] = int(merged['games'].lt(0).sum())
    audit['matched_invalid_pick'] = int((merged['pick'].notna() & ~merged['pick'].between(1, 400)).sum())
    merged = merged[merged['games'].notna() & merged['games'].ge(0) & merged['pick'].between(1, 400)]
    audit['matched_and_labeled'] = len(merged)
    merged = merged[merged['season'].between(2006, 2018)]
    audit['cohort_rows_2006_2018'] = len(merged)
    if merged.empty:
        raise ValueError('No matched cohort with measured outcome')
    merged['target'] = (merged['games'] >= 50).astype(int)
    # No athlete IDs, game outcomes or future-season features used as predictors.
    return merged.reset_index(drop=True), audit


def make_model(include_combine: bool, regularization: float):
    numeric = ['pick'] + (list(ATHLETIC_COLS) if include_combine else [])
    pre = ColumnTransformer([
        ('numeric', Pipeline([('fill', SimpleImputer(strategy='median', add_indicator=True)),
                              ('scale', StandardScaler())]), numeric),
        ('position', OneHotEncoder(handle_unknown='ignore'), ['pos']),
    ])
    return Pipeline([('pre', pre), ('clf', LogisticRegression(C=regularization, max_iter=1500, random_state=20261114))])


def metric(y, prob):
    return {'n': int(len(y)), 'positives': int(np.sum(y)),
            'roc_auc': float(roc_auc_score(y, prob)),
            'brier': float(brier_score_loss(y, prob)),
            'logloss': float(log_loss(y, prob, labels=[0, 1]))}


def validate(data: pd.DataFrame, audit: dict, hashes: dict, candidate_cs=(.1, 1., 10.)) -> dict:
    slices = {name: data[data.season.between(*span)].copy() for name, span in SPLITS.items()}
    if any(len(part) < 60 or part.target.nunique() != 2 for part in slices.values()):
        raise ValueError('Insufficient rows or class variation in chronological train/val/test')
    xcols = ['pick', 'pos', *ATHLETIC_COLS]
    for split, part in slices.items():
        if part[xcols].isna().all().any():
            raise ValueError(f'{split}: one predictor wholly unavailable')
    train, val, test = (slices[k] for k in ('train', 'validation', 'test'))
    combined = pd.concat([train, val], ignore_index=True)
    output = {
        'kind': 'ASTRA_NFL_CAREER_GAMES50_CHRONOLOGICAL_V1',
        'data_sources': {'combine': COMBINE_URL, 'draft_picks': DRAFT_URL},
        'source_sha256': hashes, 'audit': audit,
        'target': 'at least 50 lifetime NFL games through current source snapshot',
        'target_censoring_warning': 'Career totals are not equal follow-up windows; test class 2018 has at least ~7 seasons, early training classes more. Milestone sensitivity and source as-of-date required.',
        'population': 'drafted players with unambiguous same-year PFR ID and nonnull PFR games; cannot generalize to undrafted players',
        'slices': {k: {'years': list(SPLITS[k]), 'n': len(v), 'positives': int(v.target.sum())} for k,v in slices.items()},
        'train_plus_validation_n': len(combined),
        'test_seen_in_model_selection': False,
        'model_comparisons': {}, 'scientific_validation': 'PARTIAL', 'no_competition': True,
    }
    for name, include_combine in [('draft_pick_position_baseline', False), ('draft_pick_position_plus_combine', True)]:
        selection = []
        for c in candidate_cs:
            pipe = make_model(include_combine, c)
            pipe.fit(train[xcols], train.target)
            p = pipe.predict_proba(val[xcols])[:, 1]
            selection.append({'C': float(c), 'val': metric(val.target, p)})
        best = min(selection, key=lambda m: (m['val']['logloss'], m['C']))
        model = make_model(include_combine, best['C'])
        model.fit(combined[xcols], combined.target)
        prob = model.predict_proba(test[xcols])[:, 1]
        output['model_comparisons'][name] = {
            'hyperparameter_selection': selection,
            'selected_C': best['C'], 'chronological_test': metric(test.target, prob),
        }
    base = output['model_comparisons']['draft_pick_position_baseline']['chronological_test']
    extra = output['model_comparisons']['draft_pick_position_plus_combine']['chronological_test']
    output['delta_auc_with_combine'] = extra['roc_auc'] - base['roc_auc']
    output['delta_brier_with_combine'] = extra['brier'] - base['brier']
    output['delta_logloss_with_combine'] = extra['logloss'] - base['logloss']
    output['interpretation'] = ('Only if held-out metrics improve consistently and coverage is adequate may the '
                                'Combine measures add predictive value beyond draft pick + position. '
                                'No claims of causal performance effects or betting profit.')
    return output


def main():
    p=argparse.ArgumentParser(description='Public NFL Combine-to-career audit and chronological holdout')
    p.add_argument('--combine', help='Local nflverse combine.csv; otherwise downloads public release')
    p.add_argument('--draft', help='Local nflverse draft_picks.csv; otherwise downloads public release')
    p.add_argument('--output', help='Optional local aggregate JSON report')
    args=p.parse_args()
    c_raw, c_hash=load_blob(COMBINE_URL, args.combine)
    d_raw, d_hash=load_blob(DRAFT_URL, args.draft)
    c=read_csv(c_raw,SOURCE_COLS,'combine')
    d=read_csv(d_raw,DRAFT_COLS,'draft_picks')
    data, audit=prepare(c,d)
    results=validate(data,audit,{'combine':c_hash,'draft_picks':d_hash})
    result=json.dumps(results,indent=2,sort_keys=True)+'\n'
    if args.output:
        Path(args.output).write_text(result,encoding='utf-8')
    print('ASTRA_NFL_REAL_CAREER_PARTIAL HOLDOUT_N='+str(results['slices']['test']['n'])+
          ' DELTA_AUC='+str(results['delta_auc_with_combine']))
    print(result)

if __name__=='__main__': main()
