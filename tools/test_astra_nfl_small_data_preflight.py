#!/usr/bin/env python3
"""Offline safety and success tests. No Kaggle authentication required."""
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

MODULE=Path(__file__).with_name('astra_nfl_small_data_preflight.py')
spec=importlib.util.spec_from_file_location('astra_nfl_small_data_preflight',MODULE)
a=importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)

class PreflightTests(unittest.TestCase):
    def listing(self, sizes=None):
        sizes=sizes or a.SMALL_FILES
        return 'name,size,creationDate\n' + ''.join(
            f'{a.COMPETITION}/{name},{size},2026-09-28\n' for name,size in sizes.items())

    def test_real_reported_manifest(self):
        self.assertEqual(sum(a.SMALL_FILES.values()),145296)
        self.assertEqual(a.parse_official_listing(self.listing()),a.SMALL_FILES)

    def test_missing_file_rejected(self):
        data=self.listing(dict(list(a.SMALL_FILES.items())[:2]))
        with self.assertRaisesRegex(ValueError,'incomplete'):
            a.parse_official_listing(data)

    def test_changed_size_rejected(self):
        new=dict(a.SMALL_FILES);new['players.csv']=2000000
        with self.assertRaisesRegex(ValueError,'changed'):
            a.parse_official_listing(self.listing(new))

    def test_invalid_header_rejected(self):
        with self.assertRaisesRegex(ValueError,'name/size'):
            a.parse_official_listing('wrong,col\n')

    def test_duplicate_list_rejected(self):
        dup=self.listing()+f'{a.COMPETITION}/players.csv,47301,2026-09-28\n'
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            a.parse_official_listing(dup)

    def test_call_disallows_upload_and_kernel(self):
        for cmd in [['kernels','push'],['competitions','submit'],['competitions','download'],['competitions','delete']]:
            if cmd==['competitions','download']:
                continue
            with self.assertRaises(ValueError):
                a.invoke(cmd)

    def test_valid_csv(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'sample.csv';f.write_text('id,n\na,1\nb,2\n',encoding='utf-8')
            with patch.dict(a.SMALL_FILES,{'sample.csv':f.stat().st_size}):
                record=a.inspect_csv(f,'sample.csv')
                self.assertEqual(record['rows'],2)
                self.assertEqual(record['columns'],['id','n'])
                self.assertEqual(len(record['sha256']),64)

    def test_ragged_csv_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'sample.csv';f.write_text('id,n\na,1\nb\n',encoding='utf-8')
            with patch.dict(a.SMALL_FILES,{'sample.csv':f.stat().st_size}):
                with self.assertRaisesRegex(ValueError,'width'):
                    a.inspect_csv(f,'sample.csv')

    def test_zip_only_expected_member(self):
        with tempfile.TemporaryDirectory() as d:
            z=Path(d)/'file.zip'
            with zipfile.ZipFile(z,'w') as archive:archive.writestr('not-expected.csv','x\n1\n')
            with self.assertRaisesRegex(ValueError,'Unexpected ZIP member'):
                a._resolve_csv(Path(d),'players.csv')

    def test_offline_integrated_four_csv_download(self):
        with tempfile.TemporaryDirectory() as d:
            # Simulate Kaggle CLI file-list & download, preserve exact file-size guard.
            fixtures={}
            for name,size in a.SMALL_FILES.items():
                blob=b'id,value\n' + b'x,1\n' * ((size-9-4)//4)
                remainder=size-len(blob)
                blob += b'x,' + b'z' * (remainder-3) + b'\n'
                self.assertEqual(len(blob),size)
                fixtures[name]=blob
            calls=[]
            def fake(args,timeout=120):
                calls.append(args)
                if args[1]=='files':return 0,self.listing(),''
                self.assertEqual(args[:3],['competitions','download',a.COMPETITION])
                full=args[args.index('-f')+1]
                self.assertTrue(full.startswith(a.COMPETITION+'/'))
                fname=full.removeprefix(a.COMPETITION+'/');out=Path(args[args.index('-p')+1])
                (out/fname).write_bytes(fixtures[fname]);return 0,'Success',''
            with patch.object(a,'invoke',fake):
                files=a.download_small_files(Path(d))
                self.assertEqual(len(files),4)
                self.assertTrue(all(f['rows']>0 for f in files))
                self.assertEqual(len(calls),5)
                self.assertEqual([x[1] for x in calls],['files']+['download']*4)
                self.assertEqual([x[x.index('-f')+1] for x in calls[1:]],
                                 [a.COMPETITION+'/'+name for name in a.SMALL_FILES])

    def test_transport_failure_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(a,'invoke',lambda *args,**kwargs:(1,'','Permission denied')):
                with self.assertRaisesRegex(RuntimeError,'Permission denied'):
                    a.download_small_files(Path(d))


    def test_404_on_full_path_no_bulk_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            calls=[]
            def fake(args,timeout=120):
                calls.append(args)
                if args[1]=='files':return 0,self.listing(),''
                return 1,'','404 Not Found'
            with patch.object(a,'invoke',fake):
                with self.assertRaisesRegex(RuntimeError,'listed path'):
                    a.download_small_files(Path(d))
            self.assertEqual(len(calls),2)
            self.assertEqual(calls[1][calls[1].index('-f')+1],
                             a.COMPETITION+'/combine_results.csv')
            self.assertFalse(any(c[1]=='download' and '-f' not in c for c in calls))

if __name__=='__main__':unittest.main(verbosity=2)
