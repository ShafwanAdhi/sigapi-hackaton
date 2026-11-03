"""Exercise real database sessions, CSRF and region boundaries."""
import tempfile
import unittest
from uuid import uuid4
from fastapi.testclient import TestClient
from tests.test_store import DSN
from backend.mvp_store import MvpStore
from backend.web_api import create_web_app


@unittest.skipUnless(DSN, 'Requires isolated TEST_DATABASE_URL')
class AdminAuthTests(unittest.TestCase):
    def setUp(self):
        self.store = MvpStore(DSN)
        self.store.migrate()
        self.username = 'admin-' + uuid4().hex
        self.password = 'A-long-test-password-123!'
        self.store.create_admin(self.username, self.password, '35.73')
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.client = TestClient(create_web_app(self.store, self.folder.name), base_url='https://testserver')

    def login(self):
        response = self.client.post('/api/admin/auth/login', json={'username': self.username, 'password': self.password})
        self.assertEqual(response.status_code, 200, response.text)
        return {'X-CSRF-Token': response.json()['csrf_token']}

    def test_login_uses_secure_cookie_and_hashed_password(self):
        self.assertEqual(self.client.get('/api/admin/reports').status_code, 401)
        headers = self.login()
        me = self.client.get('/api/admin/auth/me')
        self.assertEqual(me.json()['region_code'], '35.73')
        with self.store.connect() as db:
            stored = db.execute('SELECT password_hash FROM admin_users WHERE username=%s', (self.username,)).fetchone()
            self.assertTrue(stored['password_hash'].startswith('$argon2id$'))
        self.assertEqual(self.client.post('/api/admin/auth/logout').status_code, 403)
        self.assertEqual(self.client.post('/api/admin/auth/logout', headers=headers).status_code, 200)
        self.assertEqual(self.client.get('/api/admin/auth/me').status_code, 401)

    def test_destination_mutations_require_csrf_and_region_scope(self):
        headers = self.login()
        body = {'name': 'Test authority', 'number': '+15550123456', 'role': 'authority',
                'categories': ['forest_land'], 'active': True, 'authorized': False}
        self.assertEqual(self.client.post('/api/admin/destinations', json=body).status_code, 403)
        created = self.client.post('/api/admin/destinations', json=body, headers=headers)
        self.assertEqual(created.status_code, 201, created.text)
        self.assertEqual(created.json()['region_code'], '35.73')
        with self.store.connect() as db:
            db.execute("INSERT INTO regions(code,name) VALUES('35.74','Other region') ON CONFLICT DO NOTHING")
            other = db.execute("INSERT INTO destinations(id,region_code,name,number,role,categories) VALUES(%s,'35.74','Other','+15550999999','authority',ARRAY['building']) RETURNING id", (uuid4(),)).fetchone()
        response = self.client.patch('/api/admin/destinations/'+str(other['id']), json=body, headers=headers)
        self.assertEqual(response.status_code, 404)
        ids = [row['id'] for row in self.client.get('/api/admin/destinations').json()['items']]
        self.assertNotIn(str(other['id']), ids)

    def test_wrong_password_and_expired_session_do_not_authorize(self):
        self.assertEqual(self.client.post('/api/admin/auth/login', json={'username': self.username, 'password': 'wrong'}).status_code, 401)
        self.assertEqual(self.client.post('/api/admin/auth/login', json={'username': 'missing-'+uuid4().hex, 'password': 'wrong'}).status_code, 401)
        self.login()
        with self.store.connect() as db:
            db.execute("UPDATE admin_sessions SET expires_at=now()-interval '1 second' WHERE user_id=(SELECT id FROM admin_users WHERE username=%s)", (self.username,))
        self.assertEqual(self.client.get('/api/admin/reports').status_code, 401)
