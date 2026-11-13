from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

MOD = Path(__file__).with_name('astra_kaggle_private_receipts.py')
spec=importlib.util.spec_from_file_location('audit',MOD)
audit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

class ReadOnlyTests(unittest.TestCase):
    def test_extract_refs_ignores_header(self):
        self.assertEqual(audit.extract_refs('ref,title\ndrstarck/nb1,Title\n'),['drstarck/nb1'])
    def test_select_exact(self):
        cfg=audit.JOBS['nfl']; self.assertEqual(audit.select([cfg['slug'],cfg['prefix']+'-renamed'],cfg),(cfg['slug'],'EXACT'))
    def test_select_renamed(self):
        cfg=audit.JOBS['nfl']; self.assertEqual(audit.select([cfg['prefix']+'-renamed'],cfg),(cfg['prefix']+'-renamed','UNIQUE_RENAMED'))
    def test_select_ambiguous(self):
        cfg=audit.JOBS['nfl']; self.assertIsNone(audit.select([cfg['prefix']+'-one',cfg['prefix']+'-two'],cfg)[0])
    def test_select_absent(self):
        cfg=audit.JOBS['nfl']; self.assertEqual(audit.select([],cfg)[1],'NOT_FOUND_IN_OWNED_LIST')
    def test_inventory_pages(self):
        calls=[]
        first='ref,title\n'+''.join(f'drstarck/n{i:02d},Some Notebook\n' for i in range(50))
        def fake(args,timeout=100):
            calls.append(args)
            return (0,first if args[args.index('--page')+1]=='1' else 'ref,title\ndrstarck/astra-nfl-2027-real-data-audit,Title\n','')
        with patch.object(audit,'call',fake):
            refs=audit.inventory()
        self.assertEqual(len(refs),51)
        self.assertEqual(len(calls),2)
    def test_wrong_account_rejected(self):
        with patch.object(audit,'call',lambda *args,**kwargs:(0,'ref,title\nwrong/nb,Title\n','')):
            with self.assertRaisesRegex(RuntimeError,'different account'):
                audit.inventory()
    def test_missing_status_no_download(self):
        cfg=audit.JOBS['bio'];calls=[]
        def fake(args,timeout=100):
            calls.append(args);return 1,'','Permission denied'
        with tempfile.TemporaryDirectory() as d,patch.object(audit,'call',fake):
            result=audit.analyze_job('bio',cfg,[cfg['slug']],Path(d))
        self.assertEqual(result['status'],'FAIL');self.assertEqual(len(calls),1)
        self.assertNotIn('output',calls[0])
    def test_receipt_valid(self):
        cfg=audit.JOBS['bio'];raw={'status':'PARTIAL','project':cfg['project'],'source':cfg['source'],
          'script_sha256':'a'*64,'gate':'PUBLIC_ARCHS4_EXPRESSION_MATRIX_QC_PASS',
          'sample_columns':903,'gene_rows':35238,'input_sha256':'b'*64}
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/cfg['receipt'];file.write_text(json.dumps(raw))
            output=audit.load_receipt(file,cfg)
        self.assertEqual(output['status'],'PARTIAL')
        self.assertEqual(output['gene_rows'],35238)
        self.assertEqual(output['science'],'UNVERIFIED')
    def test_receipt_wrong_source_rejected(self):
        cfg=audit.JOBS['bio'];raw={'project':cfg['project'],'source':'wrong','script_sha256':'a'*64}
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/cfg['receipt'];file.write_text(json.dumps(raw))
            with self.assertRaisesRegex(ValueError,'mismatch'):
                audit.load_receipt(file,cfg)
    def test_zero_submit_push_delete(self):
        self.assertEqual(audit.ALLOWED,{'list','status','files','output'})
        self.assertFalse({'push','delete','submit'} & audit.ALLOWED)

if __name__=='__main__': unittest.main(verbosity=2)
