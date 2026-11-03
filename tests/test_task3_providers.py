import unittest
from uuid import uuid4
import httpx
from backend.analysis_store import AnalysisStore
from backend.analysis_providers import DurableHTTP, extract_facts
from tests.test_store import DSN


@unittest.skipUnless(DSN,'Requires test database')
class DurableProviderTests(unittest.TestCase):
    def test_restart_cannot_reset_three_attempt_limit(self):
        store=AnalysisStore(DSN);store.migrate();key=uuid4().hex;calls=[]
        with httpx.Client(transport=httpx.MockTransport(lambda req: (calls.append(req) or httpx.Response(429,json={})))) as client:
            for _ in range(3):
                response=DurableHTTP(store,client,key,provider='test-'+key,interval=0).post('https://example.com',json={},headers={})
                self.assertEqual(response.status_code,429)
            with self.assertRaises(ValueError):
                DurableHTTP(AnalysisStore(DSN),client,key,provider='test-'+key,interval=0).post('https://example.com',json={},headers={})
        self.assertEqual(len(calls),3)

    def test_real_prompt_path_rejects_model_invented_source(self):
        value={'description_sources':[{'source_id':'missing','quote':'api membakar hutan'}],
               'time_sources':[],'category':'unknown','category_source':None}
        import json
        with httpx.Client(transport=httpx.MockTransport(lambda req:httpx.Response(200,json={'choices':[{'message':{'content':json.dumps(value)}}]}))) as client:
            with self.assertRaises(ValueError):
                extract_facts(client,'test-key','test-model',[{'id':'m','text':'halo','received_at':'2026-10-23T15:00:00Z'}])
