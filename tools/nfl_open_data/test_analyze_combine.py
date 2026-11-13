#!/usr/bin/env python3
"""Offline positive/negative tests of ASTRA Combine QC, no network."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import io

spec=importlib.util.spec_from_file_location('combine',Path(__file__).with_name('analyze_combine.py'))
a=importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
HEAD='year,player,person_id,position_group,forty_yard_dash,vertical_jump\n'

class Tests(unittest.TestCase):
    def test_valid_two_rows(self):
        b=(HEAD+'2026,Alpha,id1,WR,4.3,35\n2026,Beta,id2,WR,4.5,37\n').encode()
        r=a.analyze(b)
        self.assertEqual((r['row_count'],r['valid_40'],r['valid_vertical']),(2,2,2))
        self.assertEqual(r['position_groups'][0]['forty_median_seconds'],4.4)
        self.assertEqual(r['position_groups'][0]['vertical_median_inches'],36)
        self.assertEqual(r['competition'],'NOT_USED')
    def test_missing_metrics(self):
        r=a.analyze((HEAD+'2026,Alpha,id1,WR,,\n').encode())
        self.assertEqual((r['valid_40'],r['valid_vertical']),(0,0))
    def test_invalid_numeric_excluded(self):
        r=a.analyze((HEAD+'2026,Alpha,id1,WR,nan,999\n').encode())
        self.assertEqual((r['valid_40'],r['valid_vertical']),(0,0))
    def test_duplicate_player_year_counted(self):
        r=a.analyze((HEAD+'2026,Alpha,id1,WR,4.3,35\n2026,Beta,id1,WR,4.4,35\n').encode())
        self.assertEqual(r['duplicate_player_year'],1)
    def test_missing_position_flagged(self):
        r=a.analyze((HEAD+'2026,Alpha,id1,,4.3,35\n').encode())
        self.assertEqual(r['unclassified_position'],1)
    def test_missing_column_rejected(self):
        with self.assertRaisesRegex(ValueError,'Missing required columns'):
            a.analyze(b'year,player\n2026,Alpha\n')
    def test_ragged_rejected(self):
        with self.assertRaisesRegex(ValueError,'extra fields'):
            a.analyze((HEAD+'2026,Alpha,id1,WR,4.3,35,EXTRA\n').encode())
    def test_bad_year_rejected(self):
        with self.assertRaisesRegex(ValueError,'Unexpected year'):
            a.analyze((HEAD+'oops,Alpha,id1,WR,4.3,35\n').encode())
    def test_empty_player_rejected(self):
        with self.assertRaisesRegex(ValueError,'Unnamed player'):
            a.analyze((HEAD+'2026,,id1,WR,4.3,35\n').encode())
    def test_wrong_blob_rejected(self):
        with patch.object(a,'EXPECTED_GIT_BLOB','0'*40):
            with unittest.mock.patch.object(a.Path,'is_file',return_value=True), unittest.mock.patch.object(a.Path,'is_symlink',return_value=False), unittest.mock.patch.object(a.Path,'stat') as st, unittest.mock.patch.object(a.Path,'read_bytes',return_value=b'x'):
                st.return_value.st_size=1
                with self.assertRaisesRegex(ValueError,'changed'):
                    a.load_data('fixture.csv')
    def test_git_blob_hash_known(self):
        self.assertEqual(a.git_blob_sha1(b'hello\n'),'ce013625030ba8dba906f756967f9e9ca394464a')

if __name__=='__main__':unittest.main(verbosity=2)
