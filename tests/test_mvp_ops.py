import tempfile
import unittest
from pathlib import Path
from datetime import datetime,timedelta,timezone
from uuid import uuid4
from psycopg.types.json import Jsonb
from tests.test_store import DSN
from backend.mvp_store import MvpStore
from backend.maintenance import purge,refresh_firms


@unittest.skipUnless(DSN,'Requires separate test database')
class OperationsTests(unittest.TestCase):
    def setUp(self):
        self.store=MvpStore(DSN);self.store.migrate()
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.root=Path(self.folder.name)

    def test_purge_dry_run_then_apply_preserves_configuration_and_fresh_data(self):
        report=uuid4();account='purge-'+uuid4().hex
        with self.store.connect() as db:
            db.execute("INSERT INTO reports(id,account_id,sender_ref,conversation_id,state,created_at) VALUES(%s,%s,'private','private',%s,now()-interval '8 days')",(report,account,Jsonb({'media_ids':[]})))
        secret=self.root/'.env';secret.write_text('do-not-remove')
        self.assertGreaterEqual(purge(self.store,self.root,dry_run=True)['reports'],1)
        with self.store.connect() as db:self.assertIsNotNone(db.execute('SELECT id FROM reports WHERE id=%s',(report,)).fetchone())
        purge(self.store,self.root,dry_run=False)
        with self.store.connect() as db:
            self.assertIsNone(db.execute('SELECT id FROM reports WHERE id=%s',(report,)).fetchone())
            self.assertIsNotNone(db.execute("SELECT code FROM regions WHERE code='35.73'").fetchone())
        self.assertEqual(secret.read_text(),'do-not-remove')

    def test_firms_refresh_failure_keeps_snapshot_and_records_unavailability(self):
        with self.store.connect() as db:old=db.execute("SELECT snapshot FROM regions WHERE code='35.73'").fetchone()['snapshot']
        def failed():raise TimeoutError('fixture timeout')
        result=refresh_firms(self.store,fetch=failed)
        self.assertEqual(result['outcome'],'unavailable')
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT snapshot FROM regions WHERE code='35.73'").fetchone()['snapshot'],old)

    def test_public_activation_cannot_bypass_live_gate(self):
        with self.assertRaisesRegex(ValueError,'LIVE_GATE_REQUIRED'):
            self.store.set_settings({'public_intake':True,'live_gate_passed':False})
