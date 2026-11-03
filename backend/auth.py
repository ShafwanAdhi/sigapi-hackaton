"""Opaque revocable sessions. Session identifiers never appear in JSON."""
import hashlib
import base64
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import HTTPException
from backend.mvp_store import PASSWORDS, consume_limit


COOKIE = 'sigapi_session'
# Equal-cost verification for unknown accounts, avoiding username enumeration.
DUMMY_HASH = ('$argon2id$v=19$m=19456,t=2,p=1$'
              +base64.b64encode(b'sigapi-no-user-01').decode().rstrip('=')+'$'
              +base64.b64encode(bytes(32)).decode().rstrip('='))


def login(store, username, password, address):
    with store.connect() as db:
        allowed = consume_limit(db, 'login:'+address+':'+username.lower(), 10, 600)
        allowed = consume_limit(db, 'login-global:'+address, 100, 600) and allowed
    if not allowed:
        raise HTTPException(429, 'LOGIN_RATE_LIMITED')
    with store.connect() as db:
        user = db.execute('SELECT * FROM admin_users WHERE username=%s', (username,)).fetchone()
        try:
            verified = PASSWORDS.verify(user['password_hash'] if user else DUMMY_HASH, password)
        except (VerificationError, InvalidHashError):
            verified = False
        if not user or not user['active'] or not verified:
            raise HTTPException(401, 'INVALID_CREDENTIALS')
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        db.execute('INSERT INTO admin_sessions(token_hash,user_id,csrf_token,expires_at) VALUES(%s,%s,%s,%s)',
                   (hashlib.sha256(token.encode()).hexdigest(), user['id'], csrf,
                    datetime.now(timezone.utc)+timedelta(hours=8)))
        store.audit(db, user['id'], 'ADMIN_LOGIN', {}, str(user['id']))
    return token, csrf


def authenticate(store, request, *, mutation=False):
    token = request.cookies.get(COOKIE, '')
    if len(token) > 100:
        raise HTTPException(401, 'AUTH_REQUIRED')
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    with store.connect() as db:
        user = db.execute("""SELECT u.id,u.username,u.region_code,u.role,s.csrf_token
          FROM admin_sessions s JOIN admin_users u ON u.id=s.user_id
          WHERE s.token_hash=%s AND s.expires_at>now() AND s.last_seen>now()-interval '30 minutes'
          AND u.active""", (token_hash,)).fetchone()
        if not user:
            raise HTTPException(401, 'AUTH_REQUIRED')
        if mutation:
            supplied = request.headers.get('x-csrf-token', '')
            if not hmac.compare_digest(supplied.encode(), user['csrf_token'].encode()):
                raise HTTPException(403, 'CSRF_REQUIRED')
        db.execute('UPDATE admin_sessions SET last_seen=now() WHERE token_hash=%s', (token_hash,))
    return dict(user, token_hash=token_hash)
