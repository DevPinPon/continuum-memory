import json
import tempfile
import unittest
from pathlib import Path
from shared_memory import Memory, hermes_records, canonical_project


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'memory.db';self.store=Memory(self.path)
    def tearDown(self):self.tmp.cleanup()
    def put(self,session,text,project='D:/Demo',client='deepseek',owner='halo-primary',rid='1'):
        return self.store.capture(client,session,project,[dict(id=rid,role='user',text=text)],owner=owner)
    def find(self,query='Vega caption amber',session='new',project='D:/Demo',client='deepseek',**kw):
        return self.store.search(query,session=session,project=project,client=client,**kw)
    def test_new_session_retrieves_same_project(self):
        self.put('old','Vega caption color is amber.');self.assertTrue(self.find()['selected'])
    def test_cross_client_uses_same_memory(self):
        self.put('old','Vega caption color is amber.');r=self.find(client='hermes');self.assertEqual(r['records'][0]['sources'][0]['client'],'deepseek')
    def test_shared_visible_across_projects(self):
        self.put('old','Vega caption color is amber.',project='');self.assertTrue(self.find(project='D:/Other')['selected'])
    def test_project_isolation_even_with_identical_query(self):
        self.put('old','Vega caption color is amber.');self.assertFalse(self.find(project='D:/Other')['selected'])
    def test_owner_model_isolation(self):
        self.put('old','Vega caption color is amber.');self.assertFalse(self.find(owner='other')['selected']);self.assertFalse(self.find(model='other')['selected'])
    def test_current_session_is_not_its_own_external_evidence(self):
        self.put('old','Vega caption color is amber.');self.assertFalse(self.find(session='old')['selected'])
    def test_dedup_keeps_multiple_origins(self):
        self.put('a','Vega caption color is amber.');self.put('b','Vega caption color is amber.',client='hermes');self.assertEqual(self.store.status()['records'],1);self.assertEqual(len(self.find()['records'][0]['sources']),2)
    def test_retry_is_idempotent(self):
        self.put('a','Vega caption color is amber.');self.assertEqual(self.put('a','Vega caption color is amber.')['added'],0)
    def test_restart_is_durable(self):
        self.put('a','Vega caption color is amber.');self.store=Memory(self.path);self.assertTrue(self.find()['selected'])
    def test_sensitive_content_withheld(self):
        self.put('a','password=not-a-real-fixture-secret');self.assertEqual(self.store.status()['records'],0)
    def test_metadata_monitor_has_no_source(self):
        self.put('a','Vega private fact amber.');self.find();self.assertNotIn('Vega private',json.dumps(self.store.status()));self.assertNotIn('D:/Demo',json.dumps(self.store.status()))
    def test_explicit_correction_supersedes_previous_revision(self):
        self.store.publish('Vega caption color is amber.',fact_key='vega-caption');self.store.publish('Vega caption color is cobalt.',fact_key='vega-caption');r=self.find(query='Vega caption color');self.assertEqual(len(r['records']),1);self.assertIn('cobalt',r['records'][0]['text'])
    def test_quarantine_retracts_only_affected_source(self):
        self.put('a','Vega caption color is amber.');self.store.quarantine('deepseek','a');self.assertFalse(self.find()['selected']);self.put('b','Vega caption color is amber.');self.assertTrue(self.find()['selected'])
    def test_exact_project_aliases_only(self):
        self.put('a','Vega caption color is amber.',project='D:\\Demo\\');self.assertTrue(self.find(project='d:/demo')['selected']);self.assertFalse(self.find(project='C:/Demo')['selected'])
    def test_budget_includes_provenance(self):
        self.put('a','Vega caption color is amber.');r=self.find(max_bytes=256);self.assertLessEqual(r['evidence_bytes'],256)
    def test_completed_turn_only(self):
        msgs=[dict(role='user',content='old'),dict(role='assistant',content='partial'),dict(role='user',content='new'),dict(role='assistant',content='completed')]
        r=hermes_records(msgs);self.assertEqual([x['text']for x in r],['new','completed'])
        with self.assertRaises(ValueError):hermes_records(msgs[:-1])
    def test_rehome_removes_unknown_global_projection(self):
        self.put('a','Vega caption color is amber.',project='');self.put('a','Vega caption color is amber.',project='D:/Demo');self.assertFalse(self.find(project='D:/Other')['selected']);self.assertTrue(self.find()['selected'])
    def test_revision_republish_is_idempotent(self):
        self.store.publish('Vega amber',fact_key='vega');self.store.publish('Vega amber',fact_key='vega');self.assertEqual(self.store.status()['records'],1)

if __name__=='__main__':unittest.main()
