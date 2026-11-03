import unittest
from datetime import datetime, timezone

from backend.facts import validate_extraction, resolve_time, threat_claim, redact
from backend.decisions import decide
from backend.geospatial import region_check, firms_check


class Task3RulesTests(unittest.TestCase):
    def setUp(self):
        self.sources = [{'id':'m1','text':'Terjadi kebakaran hutan hari ini jam delapan malam',
                         'received_at':'2026-10-23T15:00:00Z'}]

    def test_extraction_must_cite_real_source_quotes(self):
        value = {'description_sources':[{'source_id':'m1','quote':'Terjadi kebakaran hutan'}],
                 'time_sources':[{'source_id':'m1','quote':'hari ini jam delapan malam'}],
                 'category':'forest_land','category_source':{'source_id':'m1','quote':'hutan'}}
        self.assertEqual(validate_extraction(value,self.sources)['category'],'forest_land')
        value['description_sources'][0]['quote']='Ada orang terjebak'
        with self.assertRaises(ValueError): validate_extraction(value,self.sources)

    def test_ai_cannot_reorder_time_corrections(self):
        sources=self.sources+[self.sources[0] | {'id':'new','text':'koreksi pukul 21.00'}]
        value={'time_sources':[{'source_id':'new','quote':'koreksi pukul 21.00'},
                               {'source_id':'m1','quote':'hari ini jam delapan malam'}]}
        checked=validate_extraction(value,sources)
        self.assertEqual(checked['time_sources'][-1]['source_id'],'new')

    def test_task3_prompt_accepts_natural_description_without_command(self):
        from backend.analysis_store import AnalysisStore
        text=AnalysisStore.natural_reply('Kirim KETERANGAN: diikuti penjelasan kejadian (minimal 10 karakter), misalnya apa yang terbakar dan kapan terlihat.')
        self.assertNotIn('KETERANGAN:',text)
        self.assertIn('Ceritakan',text)

    def test_time_without_date_needs_clarification_and_today_is_wib(self):
        self.assertIsNone(resolve_time([self.sources[0] | {'text':'mulai jam delapan malam'}]))
        self.assertEqual(resolve_time(self.sources),'2026-10-23T13:00:00+00:00')

    def test_latest_clock_correction_wins_and_multiple_clocks_need_clarification(self):
        correction=self.sources[0] | {'id':'m2','text':'koreksi mulai pukul 21.00'}
        self.assertEqual(resolve_time(self.sources+[correction]),'2026-10-23T14:00:00+00:00')
        self.assertIsNone(resolve_time([self.sources[0] | {'text':'hari ini pukul 19.00 atau pukul 20.00'}]))

    def test_negated_hypothetical_and_unrelated_risks_do_not_escalate(self):
        for text in ['tidak ada orang terjebak','jika ada orang terjebak','contoh ada orang terjebak',
                     'tidak ada korban. api tidak mengancam rumah','apakah ada orang terjebak?',
                     'kemarin ada orang terjebak, sekarang sudah aman']:
            self.assertNotEqual(threat_claim([{'id':'m','text':text}])['level'],'high',text)
        self.assertEqual(threat_claim([{'id':'m','text':'Api mengancam rumah warga'}])['level'],'high')
        self.assertEqual(threat_claim([{'id':'m','text':'ada orang terjebak di dalam rumah'}])['source_id'],'m')

    def test_later_withdrawal_overrides_previous_threat(self):
        for correction in ('Sudah aman sekarang','Semua warga sudah dievakuasi','Tidak ada orang terjebak'):
            risk=threat_claim([{'id':'old','text':'Ada orang terjebak'}, {'id':'new','text':correction}])
            self.assertNotEqual(risk['level'],'high',correction)

    def test_redaction_removes_contact_links_and_control_characters(self):
        result=redact('hubungi +628123456789 test@example.com https://example.com \x00')
        self.assertNotIn('628123456789',result);self.assertNotIn('example.com',result)
        self.assertIn('2026-10-23',redact('2026-10-23 pukul 20.00'))

    def test_public_rules_require_all_checks_but_high_risk_can_escalate(self):
        kwargs=dict(complete=True,region='inside',risk='unknown',category='forest_land',
                    time_valid=True,frames=[{'fire_visible':True,'smoke_visible':True,'image_quality':'clear'}],
                    web=['no_match'],firms='no_match',grouping=True,local_conflict=False)
        self.assertEqual(decide(**kwargs)['action'],'eligible')
        for field,value in [('web',['conflict_candidate']),('firms','unavailable'),('region','boundary'),
                            ('frames',[]),('grouping',False)]:
            self.assertEqual(decide(**(kwargs | {field:value}))['action'],'held')
        result=decide(**(kwargs | {'risk':'high','web':['unavailable'],'firms':'unavailable'}))
        self.assertTrue(result['escalate']);self.assertEqual(result['action'],'held')
        self.assertFalse(decide(**(kwargs | {'risk':'high','region':'outside'}))['escalate'])

    def test_every_frame_required_no_partial_success(self):
        result=decide(complete=True,region='inside',risk='unknown',category='forest_land',time_valid=True,
                      frames=[{'fire_visible':True,'smoke_visible':False,'image_quality':'clear'},
                              {'outcome':'unavailable'}], web=['no_match','no_match'],firms='matched',grouping=True)
        self.assertEqual(result['action'],'held')

    def test_polygon_boundary_and_stale_firms_are_not_no_match(self):
        now=datetime(2026,10,23,15,tzinfo=timezone.utc)
        region={'type':'Feature','properties':{'code':'35.73','source':'test-fixture','version':'1'},
                'geometry':{'type':'Polygon','coordinates':[[[110,-2],[112,-2],[112,0],[110,0],[110,-2]]]}}
        self.assertEqual(region_check(region,-1,111),'inside')
        self.assertEqual(region_check(region,-2,111),'boundary')
        snap={'source':'https://firms.modaps.eosdis.nasa.gov/test','sensor':'VIIRS',
              'fetched_at':'2026-10-21T00:00:00Z','coverage_start':'2026-10-20T00:00:00Z',
              'coverage_end':'2026-10-23T15:00:00Z','bbox':[110,-2,112,0],'points':[]}
        self.assertEqual(firms_check(snap,-1,111,now,now)['outcome'],'unavailable')
        snap['fetched_at']=now.isoformat()
        self.assertEqual(firms_check(snap,-1,111,now,now)['outcome'],'no_match')

    def test_firms_coverage_ends_at_real_source_time_not_http_fetch_time(self):
        now=datetime(2026,10,23,15,tzinfo=timezone.utc)
        snap={'source':'https://firms.modaps.eosdis.nasa.gov/test','sensor':'VIIRS',
              'fetched_at':now.isoformat(),'coverage_start':'2026-10-21T14:30:00Z',
              'coverage_end':'2026-10-23T14:30:00Z','bbox':[110,-2,112,0],'points':[]}
        self.assertEqual(firms_check(snap,-1,111,'2026-10-23T13:00:00Z',now)['outcome'],'no_match')
        self.assertEqual(firms_check(snap,-1,111,now,now)['outcome'],'unavailable')
