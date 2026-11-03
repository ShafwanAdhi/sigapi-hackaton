"""Validate the actual resolved deployment contract without starting Docker."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


@unittest.skipUnless(shutil.which('docker'),'Docker CLI required for Compose validation')
class DeploymentTests(unittest.TestCase):
    def test_resolved_compose_exposes_only_loopback_edge_and_bounds_memory(self):
        env=dict(os.environ)
        for key in ('SIGAPI_DB_PASSWORD','SIGAPI_DB_OWNER_PASSWORD','SIGAPI_TEST_DB_PASSWORD','INTERNAL_API_TOKEN','OPENCLAW_GATEWAY_TOKEN','SIGAPI_RATE_SALT'):
            env[key]='test-only-placeholder-credentials'
        result=subprocess.run(['docker','compose','config','--format','json'],env=env,text=True,capture_output=True,check=True)
        cfg=json.loads(result.stdout)
        services={k:v for k,v in cfg['services'].items() if not v.get('profiles')}
        self.assertLessEqual(sum(int(v['mem_limit']) for v in services.values()),2*1024**3)
        for name,service in services.items():
            if name!='edge':self.assertFalse(service.get('ports'),name)
        self.assertEqual(services['edge']['ports'][0]['host_ip'],'127.0.0.1')
        self.assertEqual(str(services['edge']['ports'][0]['published']),'8084')
        self.assertNotIn('GROQ_API_KEY',services['gateway']['environment'])
        self.assertEqual(services['gateway']['environment']['SIGAPI_WHATSAPP_OPEN'],'false')
