import io
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import career_backtest as audit


def synthetic(year_start=2006, year_end=2018, per_year=80):
    rng=np.random.default_rng(42)
    c=[];d=[]
    for year in range(year_start,year_end+1):
        for i in range(per_year):
            pid=f'Pfr{year}_{i:03d}'
            pos=['WR','RB','QB','DL','LB','DB','OL','TE'][i%8]
            forty=float(rng.normal(4.75, .28))
            vert=float(rng.normal(33, 4))
            pick=float(rng.integers(1,260))
            rating=3.5 + .02*(260-pick) + 4.0*(5-forty) + (vert-33)*.025 + float(rng.normal(0,1))
            games=int(max(0, 50 + 11*rating+float(rng.normal(0,38))-55))
            c.append(dict(season=year,player_pfr_id=pid,pos=pos,forty=forty,vertical=vert,
                          bench=25.0,broad_jump=110.,cone=7.0,shuttle=4.2))
            d.append(dict(season=year,player_pfr_id=pid,pick=pick,games=games))
    return pd.DataFrame(c),pd.DataFrame(d)

class TestBacktest(unittest.TestCase):
    def test_csv_headers_and_number_rows(self):
        c,_=synthetic(per_year=10)
        raw=c.to_csv(index=False).encode()
        result=audit.read_csv(raw,audit.SOURCE_COLS,'combine')
        self.assertEqual(len(result),130)

    def test_missing_column_rejected(self):
        with self.assertRaisesRegex(ValueError,'missing required'):
            audit.read_csv(b'a,b\n1,2\n',audit.DRAFT_COLS,'draft')

    def test_duplicate_join_id_rejected(self):
        c,d=synthetic(per_year=5)
        c=pd.concat([c,c.iloc[[0]]],ignore_index=True)
        with self.assertRaisesRegex(ValueError,'duplicate join keys'):
            audit.prepare(c,d)

    def test_unmatched_never_assumed_failure(self):
        c,d=synthetic(per_year=4)
        c=pd.concat([c,pd.DataFrame([dict(season=2010,player_pfr_id='PfrUnmatched',pos='WR',forty=4.2,vertical=33,bench=20,broad_jump=100,cone=7,shuttle=4)])],ignore_index=True)
        merged,stat=audit.prepare(c,d)
        self.assertEqual(stat['unmatched_combine_count'],1)
        self.assertNotIn('PfrUnmatched',merged['player_pfr_id'].tolist())

    def test_null_games_dropped(self):
        c,d=synthetic(per_year=4)
        d.loc[0,'games']=np.nan
        _,stat=audit.prepare(c,d)
        self.assertEqual(stat['matched_null_career_games'],1)

    def test_future_draft_cohorts_excluded(self):
        c,d=synthetic(year_start=2006,year_end=2025,per_year=4)
        merged,stat=audit.prepare(c,d)
        self.assertTrue(merged['season'].max()<=2018)

    def test_wide_dataset_clipped_metrics(self):
        c,d=synthetic(per_year=4)
        c.loc[0,'forty']=999.
        merged,_=audit.prepare(c,d)
        self.assertTrue(pd.isna(merged.iloc[0]['forty']))

    def test_holdout_models_and_delta(self):
        c,d=synthetic(per_year=80)
        merged,stat=audit.prepare(c,d)
        result=audit.validate(merged,stat,dict(combine='a'*64,draft_picks='b'*64))
        self.assertEqual(result['slices']['train']['years'],[2006,2013])
        self.assertEqual(result['slices']['validation']['years'],[2014,2015])
        self.assertEqual(result['slices']['test']['years'],[2016,2018])
        self.assertEqual(result['slices']['test']['n'],240)
        self.assertEqual(len(result['model_comparisons']),2)
        self.assertTrue(-1 <= result['delta_auc_with_combine'] <= 1)
        self.assertFalse(result['test_seen_in_model_selection'])

    def test_one_class_cohort_rejected(self):
        c,d=synthetic(per_year=80)
        d.loc[d['season'] >= 2016,'games']=0
        merged,stat=audit.prepare(c,d)
        with self.assertRaisesRegex(ValueError,'class variation'):
            audit.validate(merged,stat,{'combine':'a','draft_picks':'b'})

    def test_source_content_sha(self):
        raw=b'year,player_pfr_id\n2024,Test00\n'
        p=None
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'source.csv';p.write_bytes(raw)
            x,sha=audit.load_blob('https://irrelevant.invalid',str(p))
        self.assertEqual(x,raw)
        self.assertEqual(len(sha),64)

    def test_symlink_source_refused(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'source.csv';f.write_bytes(b'valid')
            s=Path(d)/'link.csv';s.symlink_to(f)
            with self.assertRaisesRegex(ValueError,'symlinked'):
                audit.load_blob('https://irrelevant.invalid',str(s))

    def test_no_player_identifiers_in_output(self):
        c,d=synthetic(per_year=80)
        merged,stat=audit.prepare(c,d)
        result=audit.validate(merged,stat,{'combine':'a','draft_picks':'b'},candidate_cs=(1.,))
        self.assertNotIn('Pfr2006_',str(result))
        self.assertNotIn('player_pfr_id',str(result))

    def test_negative_career_games_excluded(self):
        c,d=synthetic(per_year=4)
        d.loc[0,'games']=-1
        merged,stat=audit.prepare(c,d)
        self.assertEqual(stat['matched_negative_career_games'],1)
        self.assertEqual(len(merged),len(c)-1)

    def test_invalid_pick_excluded(self):
        c,d=synthetic(per_year=4)
        d.loc[0,'pick']=-1
        merged,stat=audit.prepare(c,d)
        self.assertEqual(stat['matched_invalid_pick'],1)
        self.assertEqual(len(merged),len(c)-1)

if __name__ == '__main__':
    unittest.main(verbosity=2)
