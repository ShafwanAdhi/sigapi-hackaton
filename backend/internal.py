"""Loopback-only Task 1 endpoint. No persistence or routing promises yet."""

import hmac
import os
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Location(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class MediaRef(BaseModel):
    model_config = ConfigDict(extra='forbid')
    kind: str = Field(max_length=40)
    content_type: str | None = Field(default=None, max_length=100)
    staged: bool = False


class InboundEvent(BaseModel):
    model_config = ConfigDict(extra='forbid')
    account_id: str = Field(min_length=1, max_length=200)
    provider_message_id: str = Field(min_length=1, max_length=300)
    sender_ref: str = Field(min_length=1, max_length=200)
    conversation_id: str = Field(min_length=1, max_length=300)
    received_at: AwareDatetime
    text: str = Field(default='', max_length=4000)
    from_me: bool = False
    location: Location | None = None
    media_refs: list[MediaRef] = Field(default_factory=list, max_length=10)


def create_app(token=None):
    token = token if token is not None else os.environ.get('INTERNAL_API_TOKEN', '')
    if len(token) < 32 or not token.isascii():
        raise ValueError('INTERNAL_API_TOKEN must contain at least 32 ASCII characters')
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    def authorize(authorization: str = Header(default='')):
        if not hmac.compare_digest(authorization.encode(), f'Bearer {token}'.encode()):
            raise HTTPException(401, 'UNAUTHORIZED')

    @app.middleware('http')
    async def body_limit(request: Request, call_next):
        if request.method == 'POST':
            size = 0
            chunks = []
            async for chunk in request.stream():
                size += len(chunk)
                if size > 64 * 1024:
                    return JSONResponse({'detail': 'BODY_TOO_LARGE'}, status_code=413)
                chunks.append(chunk)
            request._body = b''.join(chunks)
        return await call_next(request)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        # Do not reflect raw input/identifiers in error responses.
        return JSONResponse({'detail': 'INVALID_EVENT'}, status_code=422)

    @app.get('/internal/health', dependencies=[Depends(authorize)])
    def health():
        return {'mode': 'smoke', 'persistent_intake': False}

    @app.post('/internal/whatsapp/events', dependencies=[Depends(authorize)])
    def receive(event: InboundEvent):
        return {'mode': 'smoke', 'persistent_intake': False,
                'received': {'media_count': len(event.media_refs), 'location': event.location is not None},
                'reply_text': None if event.from_me else (
                    f'[UJI] Pesan diterima: {len(event.media_refs)} media; '
                    f'lokasi {"ada" if event.location else "belum ada"}. '
                    'Belum divalidasi; belum menjadi laporan tersimpan.')}

    return app
