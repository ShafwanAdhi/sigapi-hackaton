"""Authenticated loopback API. A receipt means event/job committed, not verified."""

import hashlib
import hmac
import os
from typing import Literal
from pathlib import Path
from uuid import UUID, uuid4

import psycopg
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from backend.internal import InboundEvent


class MediaToken(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: UUID


class IntakeEvent(InboundEvent):
    media_refs: list[MediaToken] = Field(default_factory=list, max_length=10)


class Claim(BaseModel):
    model_config = ConfigDict(extra='forbid')
    accounts: list[str] = Field(min_length=1, max_length=10)
    senders: list[str] = Field(default_factory=list, max_length=200)
    public_reporters: bool = False


class Admission(BaseModel):
    model_config = ConfigDict(extra='forbid')
    account_id: str = Field(min_length=1,max_length=200)
    sender_ref: str = Field(min_length=1,max_length=200)
    provider_message_id: str = Field(min_length=1,max_length=300)


class Heartbeat(BaseModel):
    model_config=ConfigDict(extra='forbid')
    service: Literal['gateway']


class Delivery(BaseModel):
    model_config = ConfigDict(extra='forbid')
    lease_token: UUID
    provider_message_id: str | None = Field(default=None, min_length=1, max_length=300)


def create_intake_app(token, store, media_root):
    if not token or len(token) < 32 or not token.isascii():
        raise ValueError('INTERNAL_API_TOKEN_REQUIRED')
    root = Path(media_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware('http')
    async def guard(request, call_next):
        if not hmac.compare_digest(request.headers.get('authorization','').encode(), ('Bearer '+token).encode()):
            return JSONResponse({'detail':'UNAUTHORIZED'}, status_code=401)
        if request.method in ('POST','PUT') and request.url.path != '/internal/media':
            chunks, size = [], 0
            async for chunk in request.stream():
                size += len(chunk)
                if size > 64 * 1024:
                    return JSONResponse({'detail':'BODY_TOO_LARGE'}, status_code=413)
                chunks.append(chunk)
            request._body = b''.join(chunks)
        return await call_next(request)

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return JSONResponse({'detail':'INVALID_EVENT'}, status_code=422)

    @app.exception_handler(psycopg.Error)
    async def database_unavailable(request, exc):
        return JSONResponse({'detail':'DATABASE_UNAVAILABLE'}, status_code=503)

    @app.get('/internal/health')
    def health():
        with store.connect() as db:
            db.execute('SELECT version FROM schema_versions WHERE version=1').fetchone()
        return {'mode':'intake', 'persistent_intake':True}

    @app.post('/internal/whatsapp/events', status_code=202)
    def receive(event: IntakeEvent):
        if event.from_me:
            return {'mode':'ignored','persistent_intake':False}
        if hasattr(store,'admit'):
            store.admit(event.account_id,event.sender_ref,event.provider_message_id)
        try:
            return store.accept(event.model_dump(mode='json'))
        except ValueError:
            raise HTTPException(422, 'INVALID_EVENT_REFERENCE') from None

    @app.post('/internal/admission')
    def admission(body: Admission):
        if not hasattr(store,'admit'):raise HTTPException(503,'PUBLIC_INTAKE_UNAVAILABLE')
        store.admit(body.account_id,body.sender_ref,body.provider_message_id)
        return {'admitted':True}

    @app.post('/internal/heartbeat')
    def heartbeat(body:Heartbeat):
        if hasattr(store,'beat'):store.beat(body.service)
        return {'recorded':hasattr(store,'beat')}

    @app.post('/internal/media', status_code=201)
    async def upload(request: Request, x_account_id: str = Header(min_length=1,max_length=200),
                     x_sender_ref: str = Header(min_length=1,max_length=200),
                     x_provider_message_id: str = Header(min_length=1,max_length=300),
                     x_media_slot: int = Header(ge=0,le=9), x_media_kind: str = Header()):
        if x_media_kind not in ('image','video'):
            raise HTTPException(422, 'UNSUPPORTED_MEDIA_KIND')
        id = uuid4()
        suffix = '.jpg' if x_media_kind == 'image' else '.mp4'
        path = root / (str(id) + suffix)
        temporary = path.with_suffix('.part')
        size, digest = 0, hashlib.sha256()
        limit = (10 if x_media_kind == 'image' else 20) * 1024 * 1024
        try:
            with temporary.open('xb') as file:
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > limit:
                        raise HTTPException(413, 'MEDIA_TOO_LARGE')
                    digest.update(chunk); file.write(chunk)
                file.flush(); os.fsync(file.fileno())
            if not size:
                raise HTTPException(422, 'EMPTY_MEDIA')
            # Serialize replays of the same upload slot; never overwrite a different file.
            with store.connect() as db:
                db.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',
                           (repr((x_account_id,x_sender_ref,x_provider_message_id,x_media_slot)),))
                old = db.execute('SELECT id,sha256 FROM media WHERE account_id=%s AND sender_ref=%s AND provider_message_id=%s AND slot=%s',
                                 (x_account_id,x_sender_ref,x_provider_message_id,x_media_slot)).fetchone()
                if old:
                    if old['sha256'] != digest.hexdigest():
                        raise HTTPException(409, 'MEDIA_SLOT_CONFLICT')
                    return {'id':str(old['id'])}
                temporary.replace(path)
                db.execute('''INSERT INTO media(id,account_id,sender_ref,provider_message_id,slot,kind,sha256,storage_key,content_type)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                           (id,x_account_id,x_sender_ref,x_provider_message_id,x_media_slot,x_media_kind,
                            digest.hexdigest(),path.name,'application/octet-stream'))
            return {'id':str(id)}
        finally:
            temporary.unlink(missing_ok=True)

    @app.post('/internal/outbox/claim')
    def claim(body: Claim):
        row = (store.claim_outbox(body.accounts,body.senders,public_reporters=True) if body.public_reporters
               else store.claim_outbox(body.accounts, body.senders))
        if not row:
            return {'item':None}
        return {'item':dict({k:row[k] for k in ['id','account_id','sender_ref','text','lease_token']},recipient_authorized=True)}

    @app.post('/internal/outbox/{id}/start')
    def start(id: UUID, body: Delivery):
        started=store.start_send(id,body.lease_token)
        result={'started':started}
        if started and hasattr(store,'admitted_text'):
            result['text']=store.admitted_text(id,body.lease_token)
        return result

    @app.post('/internal/outbox/{id}/finish')
    def finish(id: UUID, body: Delivery):
        return {'recorded':store.finish_send(id,body.lease_token,body.provider_message_id)}

    return app
