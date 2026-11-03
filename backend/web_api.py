"""Public and authenticated web API; never mounts the transport API."""
import re
import os
from pathlib import Path
from uuid import UUID, uuid4
import psycopg
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from backend import auth


class LoginBody(BaseModel):
    model_config = ConfigDict(extra='forbid')
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class DestinationBody(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=1, max_length=150)
    number: str = Field(pattern=r'^\+[1-9][0-9]{7,14}$')
    role: str = Field(pattern=r'^(authority|community)$')
    categories: list[str] = Field(min_length=1, max_length=2)
    active: bool = False
    authorized: bool = False
    address: str = Field(default='', max_length=500)
    invitation_url: str = Field(default='', max_length=500)


class TestSend(BaseModel):
    model_config=ConfigDict(extra='forbid')
    request_id: UUID


def create_web_app(store, media_root, *, secure_cookies=True):
    root = Path(media_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return JSONResponse({'detail':'INVALID_INPUT'}, status_code=422)

    @app.exception_handler(psycopg.Error)
    async def unavailable(request, exc):
        return JSONResponse({'detail':'DATABASE_UNAVAILABLE'}, status_code=503)

    @app.middleware('http')
    async def headers(request, call_next):
        if request.method not in ('GET','HEAD','OPTIONS'):
            origin=request.headers.get('origin')
            expected=os.environ.get('SIGAPI_PUBLIC_URL',str(request.base_url).rstrip('/'))
            if origin and origin!=expected:
                return JSONResponse({'detail':'ORIGIN_NOT_ALLOWED'},status_code=403)
        if request.url.path.startswith('/api/admin/') and request.url.path != '/api/admin/auth/login':
            try:
                request.state.admin = auth.authenticate(store, request, mutation=request.method not in ('GET','HEAD','OPTIONS'))
            except HTTPException as exc:
                return JSONResponse({'detail':exc.detail}, status_code=exc.status_code)
        if request.method in ('POST','PATCH','PUT'):
            limit=11*1024*1024 if request.url.path.endswith('/verifications') else 64*1024
            size=0;chunks=[]
            async for chunk in request.stream():
                size+=len(chunk)
                if size>limit:
                    return JSONResponse({'detail':'BODY_TOO_LARGE'},status_code=413)
                chunks.append(chunk)
            request._body=b''.join(chunks)
        response = await call_next(request)
        response.headers.update({'Cache-Control':'no-store', 'X-Content-Type-Options':'nosniff',
                                 'Referrer-Policy':'no-referrer'})
        return response

    @app.get('/healthz')
    def health():
        with store.connect() as db:
            db.execute('SELECT 1')
        return {'status':'ok'}

    @app.get('/api/laporan/{slug}')
    def public_overview(slug: str):
        from backend.public import overview
        return overview(store,slug)

    @app.post('/api/laporan/{slug}/verifications',status_code=201)
    async def verification(slug: str,request: Request):
        from backend.public import submit
        async with request.form(max_files=1,max_fields=12) as form:
            upload=form.get('photo')
            if upload is not None and not hasattr(upload,'read'):
                raise HTTPException(422,'INVALID_PHOTO')
            photo=await upload.read(10*1024*1024+1) if upload else None
            values={k:v for k,v in form.items() if k!='photo'}
            return submit(store,root,slug,values,photo,request.client.host)

    @app.get('/api/laporan/{slug}/photo')
    def public_photo(slug: str):
        from backend.public import public_incident
        with store.connect() as db:
            row=public_incident(db,slug)
        key=row['photo_key']
        if not key or not re.fullmatch(r'public-[a-f0-9-]{36}\.jpg',key) or not (root/key).is_file():
            raise HTTPException(404,'NOT_FOUND')
        return FileResponse(root/key,media_type='image/jpeg',headers={'Cache-Control':'no-store'})

    @app.post('/api/admin/auth/login')
    def sign_in(body: LoginBody, request: Request):
        token, csrf = auth.login(store, body.username, body.password, request.client.host)
        response = JSONResponse({'csrf_token':csrf})
        response.set_cookie(auth.COOKIE, token, secure=secure_cookies, httponly=True,
                            samesite='strict', max_age=28800, path='/api/admin')
        return response

    @app.get('/api/admin/auth/me')
    def me(request: Request):
        return {k:v for k,v in request.state.admin.items() if k not in ('token_hash',)}

    @app.post('/api/admin/auth/logout')
    def sign_out(request: Request):
        with store.connect() as db:
            db.execute('DELETE FROM admin_sessions WHERE token_hash=%s', (request.state.admin['token_hash'],))
        response = JSONResponse({'logged_out':True})
        response.delete_cookie(auth.COOKIE, path='/api/admin', secure=secure_cookies, httponly=True, samesite='strict')
        return response

    @app.get('/api/admin/reports')
    def reports(request: Request):
        with store.connect() as db:
            rows = db.execute('SELECT id,status,created_at,region_code,revision,incident_id FROM reports WHERE region_code=%s ORDER BY created_at DESC LIMIT 100',
                              (request.state.admin['region_code'],)).fetchall()
        return {'items':rows}

    @app.get('/api/admin/destinations')
    def destinations(request: Request):
        with store.connect() as db:
            rows = db.execute('SELECT * FROM destinations WHERE region_code=%s ORDER BY name,id', (request.state.admin['region_code'],)).fetchall()
        return {'items':rows}

    def save_destination(body, request, destination_id=None):
        if any(c not in ('forest_land','building') for c in body.categories):
            raise HTTPException(422, 'INVALID_CATEGORY')
        if body.invitation_url and not body.invitation_url.startswith('https://whatsapp.com/channel/'):
            raise HTTPException(422, 'INVALID_INVITATION_URL')
        user = request.state.admin
        with store.connect() as db:
            if destination_id:
                row = db.execute('SELECT * FROM destinations WHERE id=%s AND region_code=%s FOR UPDATE',
                                 (destination_id,user['region_code'])).fetchone()
                if not row:
                    raise HTTPException(404, 'NOT_FOUND')
                db.execute("UPDATE outbox SET state='cancelled',reason='DESTINATION_CHANGED' WHERE destination_id=%s AND state IN ('pending','leased')", (str(destination_id),))
                row = db.execute('''UPDATE destinations SET name=%s,number=%s,role=%s,categories=%s,active=%s,
                  authorized=%s,address=%s,invitation_url=%s,version=version+1,updated_at=now() WHERE id=%s RETURNING *''',
                  (body.name,body.number,body.role,body.categories,body.active,body.authorized,body.address,body.invitation_url,destination_id)).fetchone()
            else:
                destination_id = uuid4()
                row = db.execute('''INSERT INTO destinations(id,region_code,name,number,role,categories,active,authorized,address,invitation_url)
                  VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *''',
                  (destination_id,user['region_code'],body.name,body.number,body.role,body.categories,body.active,body.authorized,body.address,body.invitation_url)).fetchone()
            store.audit(db, destination_id, 'DESTINATION_SAVED', {'region_code':user['region_code'],'version':row['version']}, str(user['id']))
        return row

    @app.post('/api/admin/destinations', status_code=201)
    def create_destination(body: DestinationBody, request: Request):
        return save_destination(body, request)

    @app.patch('/api/admin/destinations/{id}')
    def update_destination(id: UUID, body: DestinationBody, request: Request):
        return save_destination(body, request, id)

    @app.post('/api/admin/destinations/{id}/test',status_code=202)
    def test_send(id:UUID,body:TestSend,request:Request):
        user=request.state.admin
        with store.connect() as db:
            dest=db.execute('SELECT * FROM destinations WHERE id=%s AND region_code=%s FOR UPDATE',(id,user['region_code'])).fetchone()
            if not dest:raise HTTPException(404,'NOT_FOUND')
            if not dest['active'] or not dest['authorized']:raise HTTPException(422,'AUTHORIZED_ACTIVE_RECIPIENT_REQUIRED')
            key='configuration-test:'+str(id)+':'+str(body.request_id)
            old=db.execute('SELECT id FROM outbox WHERE source_key=%s',(key,)).fetchone()
            if old:return {'outbox_id':old['id'],'replayed':True}
            outbox=uuid4()
            db.execute('''INSERT INTO outbox(id,account_id,sender_ref,text,source_key,audience,destination_id,destination_version)
              VALUES(%s,%s,%s,%s,%s,'configuration_test',%s,%s)''',(outbox,dest['account_id'],dest['number'],
              '[UJI SIGAPI] Pemeriksaan konfigurasi penerima. Ini bukan laporan kebakaran atau permintaan tindakan.',key,str(id),dest['version']))
            store.audit(db,id,'TEST_SEND_REQUESTED',{'outbox_id':str(outbox),'region_code':user['region_code']},str(user['id']))
        return {'outbox_id':outbox,'replayed':False}

    from backend.admin_api import install_admin_routes
    install_admin_routes(app,store,root)
    return app
