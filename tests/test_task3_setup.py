import json
import tempfile
import unittest
from pathlib import Path
from backend.task3_config import Task3Config


class SetupTests(unittest.TestCase):
    def test_malformed_config_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'config.json';cfg=Task3Config(path)
            for value in ({'distribution_enabled':True,'destinations':3},{'distribution_enabled':True,'destinations':None},[]):
                path.write_text(json.dumps(value));self.assertEqual(cfg.destinations(),{})

    def test_real_snapshot_import_rejects_non_nasa_or_stale_source(self):
        from backend.task3_data import parse_firms
        from datetime import datetime,timezone
        now=datetime(2026,10,23,15,tzinfo=timezone.utc)
        with self.assertRaises(ValueError):parse_firms(b'latitude,longitude,acq_date,acq_time\n',{'last-modified':'Thu, 01 Oct 2026 12:00:00 GMT'},now)
        result=parse_firms(b'latitude,longitude,acq_date,acq_time\n-7.95,112.60,2026-10-23,1200\n',{'last-modified':'Fri, 23 Oct 2026 14:00:00 GMT'},now)
        self.assertEqual(len(result['points']),1)
        self.assertEqual(result['sensor'],'VIIRS')
