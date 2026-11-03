"""Real local HTTP + Node bridge + PostgreSQL; no WhatsApp/provider sends."""

import os
from pathlib import Path
import socket
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
from uuid import uuid4

from PIL import Image
import uvicorn

from backend.intake_api import create_intake_app
from backend.store import Store
from backend.worker import validate_media
from tests.test_store import DSN

ROOT = Path(__file__).resolve().parents[1]
NODE = Path(shutil.which('node') or ROOT / '.runtime/node/package/bin/node.exe')


@unittest.skipUnless(DSN and NODE.is_file(), 'Requires test DB and local Node')
class TransportEndToEndTests(unittest.TestCase):
    def test_lost_receipt_restart_and_complete_report_through_real_http(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            incoming = root / 'incoming'; incoming.mkdir()
            Image.new('RGB', (32, 32)).save(incoming / 'photo.jpg')
            account = 'e2e-' + uuid4().hex
            store = Store(DSN); store.migrate()
            app = create_intake_app('x' * 32, store, root / 'stored')
            sock = socket.socket(); sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
            server = uvicorn.Server(uvicorn.Config(app, log_level='critical', access_log=False))
            thread = threading.Thread(target=lambda: server.run(sockets=[sock]), daemon=True)
            thread.start()
            try:
                for _ in range(100):
                    if server.started:
                        break
                    time.sleep(.05)
                self.assertTrue(server.started)
                script = r'''
                  import {createIntakeBridge} from './openclaw-plugin/intake.js';
                  import path from 'node:path';
                  const base=process.env.SIGAPI_TEST_ROOT;
                  let loseReceipt=true;
                  const options={token:'x'.repeat(32),accounts:[process.env.SIGAPI_TEST_ACCOUNT],allowSenders:['test-only'],
                    spoolRoot:path.join(base,'spool'),mediaRoot:path.join(base,'incoming'),
                    fetchImpl:async(url,opts)=>{
                      const response=await fetch(url.replace(':8011',':'+process.env.SIGAPI_TEST_PORT),opts);
                      if(url.endsWith('/events')&&loseReceipt){loseReceipt=false;await response.text();throw Error('lost receipt');}
                      return response;
                    }};
                  const events=[{content:'REPORT'},
                    {content:'KETERANGAN: Sampel uji api di pepohonan',media:[{kind:'image',path:path.join(base,'incoming/photo.jpg')}]},
                    {content:'',location:{latitude:-1,longitude:110}},
                    {content:'KONFIRMASI LOKASI 1'}];
                  for(let i=0;i<events.length;i++){
                    const bridge=createIntakeBridge(options); // simulate transport restart
                    const ctx={channelId:'whatsapp',accountId:process.env.SIGAPI_TEST_ACCOUNT,
                      senderId:'test-only',conversationId:'test-chat',messageId:'event-'+i};
                    bridge.received(events[i],ctx);await bridge.dispatch({},ctx);
                  }
                  await createIntakeBridge(options).flushSpool();
                '''
                result = subprocess.run([str(NODE), '--input-type=module', '-e', script], cwd=ROOT,
                    env=dict(os.environ, SIGAPI_TEST_ROOT=str(root), SIGAPI_TEST_ACCOUNT=account,
                             SIGAPI_TEST_PORT=str(port)), capture_output=True, timeout=40)
                self.assertEqual(result.returncode, 0, result.stderr.decode()[:1000])
                for _ in range(4):
                    self.assertTrue(Store(DSN).run_once(account=account,
                        validate=lambda row: validate_media(row, root / 'stored')))
                report = Store(DSN).active_report(account, 'test-only')
                self.assertEqual(report['status'], 'complete')
                self.assertTrue(report['state']['location_confirmed'])
                self.assertFalse(report['state']['consent_contact'])
                self.assertEqual(len(report['state']['media_ids']), 1)
                with store.connect() as db:
                    for table in ['inbound_events', 'jobs', 'outbox']:
                        n = db.execute(f'SELECT count(*) n FROM {table} WHERE account_id=%s', (account,)).fetchone()['n']
                        self.assertEqual(n, 4)
                    self.assertEqual(db.execute('SELECT count(*) n FROM reports WHERE account_id=%s', (account,)).fetchone()['n'], 1)
            finally:
                server.should_exit = True
                thread.join(10)
                sock.close()
