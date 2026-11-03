"""Local operator commands. Secrets remain in .env/ADC."""

import argparse
import json
import os
import re
import secrets
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

from backend.providers import ProviderUnavailable, groq_observe, web_detect
from backend.smoke import VisionBudget
from backend.web_evidence import LocalImageIndex, SerpApiBudget, check_image_evidence, serpapi_detect

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / '.runtime'
NODE = RUNTIME / 'node/package/bin/node.exe'
OPENCLAW = RUNTIME / 'openclaw/node_modules/openclaw/openclaw.mjs'
CONFIG = RUNTIME / 'openclaw-state/openclaw.json'


def configure(team_number):
    if not re.fullmatch(r'\+[1-9][0-9]{7,14}', team_number):
        raise ValueError('Nomor uji wajib format E.164, misalnya +62...')
    if CONFIG.exists():
        raise ValueError('Konfigurasi sudah ada; periksa lokal tanpa menimpanya otomatis')
    env_path = ROOT / '.env'
    if not env_path.exists():
        with env_path.open('x', encoding='utf-8') as file:
            file.write(f'INTERNAL_API_TOKEN={secrets.token_urlsafe(32)}\n'
                       f'OPENCLAW_GATEWAY_TOKEN={secrets.token_urlsafe(32)}\n'
                       'GROQ_API_KEY=\nGROQ_VISION_MODEL=\nSERPAPI_API_KEY=\n'
                       'ENABLE_GOOGLE_VISION=false\nGOOGLE_CLOUD_PROJECT=\n')
    load_dotenv(env_path, interpolate=False)
    if len(os.environ.get('OPENCLAW_GATEWAY_TOKEN', '')) < 32:
        raise ValueError('Isi OPENCLAW_GATEWAY_TOKEN lokal dengan token acak minimal 32 karakter')
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    config = {
        'gateway': {'mode': 'local', 'bind': 'loopback', 'auth': {
            'mode': 'token', 'token': '${OPENCLAW_GATEWAY_TOKEN}'}},
        'channels': {'whatsapp': {'dmPolicy': 'allowlist', 'allowFrom': [team_number],
            'groupPolicy': 'disabled', 'selfChatMode': False, 'pluginHooks': {'messageReceived': True}}},
        'plugins': {'allow': ['whatsapp', 'sigapi-validation-demo'], 'load': {'paths': [
            str(ROOT / 'openclaw-plugin'), str(RUNTIME / 'openclaw/node_modules/@openclaw/whatsapp')]},
            'entries': {'whatsapp': {'enabled': True}, 'sigapi-validation-demo': {
                'enabled': True, 'config': {'allowSenders': [team_number]}}}},
    }
    with CONFIG.open('x', encoding='utf-8') as file:
        json.dump(config, file, indent=2)
    print('Konfigurasi lokal dibuat. Isi .env; jangan kirim secret/QR ke chat.')


def readiness():
    status = {name: bool(os.environ.get(name)) for name in [
        'INTERNAL_API_TOKEN', 'OPENCLAW_GATEWAY_TOKEN', 'GROQ_API_KEY',
        'GROQ_VISION_MODEL']}
    vision_ready = False
    if vision_enabled():
        try:
            import google.auth
            google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
            vision_ready = bool(os.environ.get('GOOGLE_CLOUD_PROJECT'))
        except Exception:
            pass
    status['web_provider_configured'] = bool(os.environ.get('SERPAPI_API_KEY')) or vision_ready
    status.update(node_local=NODE.exists(), openclaw_installed=OPENCLAW.exists(),
                  openclaw_config=CONFIG.exists(), ffmpeg=bool(shutil.which('ffmpeg')),
                  ffprobe=bool(shutil.which('ffprobe')))
    print(json.dumps(status, indent=2))
    return 0 if all(status.values()) else 1


def vision_enabled():
    return os.environ.get('ENABLE_GOOGLE_VISION', '').lower() == 'true'


def vision_check(data, client, budget):
    if not vision_enabled():
        raise ProviderUnavailable('VISION_DISABLED')
    project = os.environ.get('GOOGLE_CLOUD_PROJECT')
    if not project:
        raise ProviderUnavailable('VISION_NOT_CONFIGURED')
    try:
        import google.auth
        from google.auth.transport.requests import Request
        credentials, _ = google.auth.default(
            scopes=['https://www.googleapis.com/auth/cloud-platform'], quota_project_id=project)
        credentials.refresh(Request())
    except Exception:
        raise ProviderUnavailable('VISION_AUTH_UNAVAILABLE') from None
    try:
        return web_detect(data, client, budget, {
            'Authorization': f'Bearer {credentials.token}', 'x-goog-user-project': project})
    except ValueError as exc:
        if str(exc) == 'VISION_BUDGET_EXHAUSTED':
            raise ProviderUnavailable('VISION_BUDGET_EXHAUSTED') from None
        raise


def provider_smoke(args):
    from backend.media import sample_media
    frames = sample_media(Path(args.image))
    run = {'checked_at': datetime.now(timezone.utc).isoformat(), 'test_case': args.case,
           'mode': 'live_provider_smoke', 'groq_model': os.environ.get('GROQ_VISION_MODEL'),
           'frames': [], 'limitations': 'Observasi terbatas pada gambar/frame; bukan bukti keaslian atau keputusan publikasi.'}
    budget = VisionBudget(RUNTIME / 'vision-budget.sqlite3')
    search_budget = SerpApiBudget(RUNTIME / 'serpapi-budget.sqlite3')
    index = LocalImageIndex(RUNTIME / 'smoke-image-index.sqlite3')
    run_id = secrets.token_hex(8)
    failed = False
    # Ordinary operator environment controls proxy/TLS; never disable certificate verification.
    with httpx.Client() as client:
        for position, data in enumerate(frames):
            frame = {}
            if args.provider in ('groq', 'both'):
                if position:
                    # Free-plan smoke: at most two new frame starts per minute in this run.
                    # Other processes/account usage can still exhaust quota; keep unavailable honest.
                    print('Jeda Groq Free Plan 35 detik sebelum frame berikutnya.', flush=True)
                    time.sleep(35)
                try:
                    frame['groq'] = groq_observe(data, client, os.environ.get('GROQ_API_KEY'), os.environ.get('GROQ_VISION_MODEL'))
                except ProviderUnavailable as exc:
                    frame['groq'] = {'outcome': 'unavailable', 'reason': str(exc)}
                    failed = True
            if args.provider in ('web', 'serpapi', 'vision', 'both'):
                key = os.environ.get('SERPAPI_API_KEY')
                search = (lambda: serpapi_detect(data, client, search_budget, key)) if key and args.provider != 'vision' else None
                frame['evidence'] = check_image_evidence(data, index, serpapi=search,
                    vision=lambda: vision_check(data, client, budget),
                    vision_enabled=vision_enabled() and args.provider != 'serpapi')
                failed |= frame['evidence']['web']['outcome'] == 'unavailable'
                index.add(f'{run_id}:{position}', data)
            run['frames'].append(frame)
    RUNTIME.mkdir(exist_ok=True)
    output = RUNTIME / f'smoke-{secrets.token_hex(8)}.json'
    output.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Hasil pemeriksaan tersimpan lokal: {output}')
    print('Ada provider belum tersedia; periksa hasil dan manual_review.' if failed else 'Provider yang diminta merespons; bukan izin publikasi.')
    return 1 if failed else 0


def main():
    load_dotenv(ROOT / '.env', interpolate=False)
    ffmpeg_bin = RUNTIME / 'ffmpeg/bin'
    if ffmpeg_bin.exists():
        os.environ['PATH'] = str(ffmpeg_bin) + os.pathsep + os.environ.get('PATH', '')
    parser = argparse.ArgumentParser(description='SIGAPI demo verifikasi; belum sistem produksi')
    commands = parser.add_subparsers(dest='command', required=True)
    config = commands.add_parser('configure')
    config.add_argument('--team-number', required=True)
    commands.add_parser('readiness')
    serve = commands.add_parser('serve')
    serve.add_argument('--port', type=int, default=8011)
    serve.add_argument('--smoke', action='store_true', help='API metadata Task 1, bukan intake persisten')
    commands.add_parser('db-start')
    commands.add_parser('migrate')
    worker = commands.add_parser('worker')
    worker.add_argument('--once', action='store_true')
    commands.add_parser('intake-status')
    analysis=commands.add_parser('analysis-worker')
    analysis.add_argument('--once',action='store_true')
    commands.add_parser('task3-init')
    commands.add_parser('task3-status')
    data=commands.add_parser('task3-fetch');data.add_argument('kind',choices=['region','firms'])
    region=commands.add_parser('task3-approve-region');region.add_argument('--sha256',required=True);region.add_argument('--reason',required=True)
    analyze=commands.add_parser('analyze');analyze.add_argument('report_id')
    inspect=commands.add_parser('report-inspect');inspect.add_argument('report_id');inspect.add_argument('--output',required=True)
    review=commands.add_parser('review-evidence');review.add_argument('report_id');review.add_argument('--key',required=True);review.add_argument('--reason',required=True);review.add_argument('--reference',action='append',required=True)
    group=commands.add_parser('review-incident');group.add_argument('report_id');group.add_argument('--merge-into');group.add_argument('--reason',required=True)
    rec=commands.add_parser('reconcile-delivery');rec.add_argument('outbox_id');rec.add_argument('--reason',required=True)
    choice=rec.add_mutually_exclusive_group(required=True);choice.add_argument('--receipt');choice.add_argument('--retry',action='store_true')
    smoke = commands.add_parser('providers')
    smoke.add_argument('--image', required=True, help='Foto/video berizin di disk lokal')
    smoke.add_argument('--case', required=True, choices=['fire', 'no_fire', 'blurred', 'web_known', 'video'])
    smoke.add_argument('--provider', choices=['groq', 'web', 'serpapi', 'vision', 'both'], default='both')
    claw = commands.add_parser('openclaw')
    claw.add_argument('args', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        if args.command == 'configure':
            configure(args.team_number)
        elif args.command == 'readiness':
            return readiness()
        elif args.command == 'providers':
            return provider_smoke(args)
        elif args.command == 'serve':
            import uvicorn
            if args.smoke:
                from backend.internal import create_app
                app = create_app()
            else:
                from backend.intake_api import create_intake_app
                from backend.analysis_store import AnalysisStore as Store
                app = create_intake_app(os.environ.get('INTERNAL_API_TOKEN'),
                                        Store(os.environ.get('DATABASE_URL')), RUNTIME / 'intake-media')
            uvicorn.run(app, host='127.0.0.1', port=args.port, access_log=False)
        elif args.command == 'db-start':
            pg_ctl = Path(os.environ.get('SIGAPI_PG_CTL', 'C:/Program Files/PostgreSQL/16/bin/pg_ctl.exe'))
            data = RUNTIME / 'postgres-intake/data'
            if not pg_ctl.is_file() or not (data / 'PG_VERSION').is_file():
                raise ValueError('CLUSTER_LOKAL_BELUM_TERSEDIA; lihat panduan Task 2')
            opts = dict(stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), timeout=90)
            if subprocess.run([str(pg_ctl), '-D', str(data), 'status'], **opts).returncode != 0:
                result = subprocess.run([str(pg_ctl), '-D', str(data), '-l',
                    str(data.parent / 'server.log'), '-w', 'start'], **opts)
                if result.returncode:
                    raise ValueError('POSTGRES_START_FAILED; periksa log lokal')
            print('PostgreSQL demo lokal aktif (cluster privat; loopback port 55432).')
        elif args.command.startswith('task3-') or args.command in ('analysis-worker','analyze','report-inspect','review-evidence','review-incident','reconcile-delivery'):
            from backend.analysis_store import AnalysisStore
            from backend.task3_config import Task3Config
            from backend.task3_data import bootstrap,fetch_data,approve_region,status,save_json
            from backend.operator import inspect_report,review_evidence,group_incident,reconcile
            from uuid import UUID
            cfg=Task3Config();store=AnalysisStore(os.environ.get('DATABASE_URL'),cfg)
            if args.command=='task3-init':
                bootstrap();print('Konfigurasi privat Task 3 tersedia; pengiriman belum diaktifkan.')
            elif args.command=='task3-fetch':print(json.dumps(fetch_data(cfg,args.kind),indent=2))
            elif args.command=='task3-approve-region':
                approve_region(cfg,args.sha256,args.reason);print('Review batas wilayah disimpan. Pengiriman mengikuti konfigurasi privat.')
            elif args.command=='task3-status':print(json.dumps(status(store,cfg),indent=2))
            elif args.command=='analysis-worker':
                from backend.analysis_engine import AnalysisEngine,run_analysis_worker
                print('Worker pemeriksaan aktif; distribusi tetap mengikuti konfigurasi privat.',flush=True)
                run_analysis_worker(AnalysisEngine(store,RUNTIME/'intake-media',cfg),once=args.once)
            elif args.command=='analyze':
                store.opt_in(UUID(args.report_id));print('Analisis laporan dipilih operator; pekerjaan terantre, belum dikirim.')
            elif args.command=='report-inspect':
                output=Path(args.output)
                if output.exists():raise ValueError('OUTPUT_EXISTS')
                output.parent.mkdir(parents=True,exist_ok=True)
                output.write_text(json.dumps(inspect_report(store,UUID(args.report_id)),default=str,ensure_ascii=False,indent=2),encoding='utf-8')
                print('Hasil inspeksi privat tersimpan; berisi input pelapor, jangan dipublikasikan.')
            elif args.command=='review-evidence':review_evidence(store,UUID(args.report_id),args.key,args.reason,args.reference)
            elif args.command=='review-incident':group_incident(store,UUID(args.report_id),UUID(args.merge_into) if args.merge_into else None,args.reason)
            elif args.command=='reconcile-delivery':reconcile(store,UUID(args.outbox_id),args.reason,args.receipt,args.retry)
        elif args.command in ('migrate', 'worker', 'intake-status'):
            from backend.analysis_store import AnalysisStore as Store
            store = Store(os.environ.get('DATABASE_URL'))
            if args.command == 'migrate':
                store.migrate()
                print('Migrasi intake selesai; data lama dipertahankan.')
            elif args.command == 'worker':
                from backend.worker import run_worker
                print('Worker intake aktif; Ctrl+C untuk berhenti.', flush=True)
                run_worker(store, RUNTIME / 'intake-media', once=args.once)
            else:
                with store.connect() as db:
                    status = {'reports': db.execute('SELECT status,count(*) n FROM reports GROUP BY status').fetchall()}
                    for table in ['jobs', 'outbox']:
                        status[table] = db.execute(f'SELECT state,count(*) n FROM {table} GROUP BY state').fetchall()
                print(json.dumps(status, indent=2))
        elif args.command == 'openclaw':
            if not NODE.exists() or not OPENCLAW.exists():
                raise ValueError('OpenClaw/Node lokal belum terpasang lengkap')
            env = dict(os.environ, OPENCLAW_STATE_DIR=str(CONFIG.parent), OPENCLAW_CONFIG_PATH=str(CONFIG),
                       PATH=str(NODE.parent) + os.pathsep + os.environ['PATH'])
            # Transport process does not need provider credentials.
            for name in list(env):
                if name.endswith('_API_KEY') or name in ('GOOGLE_APPLICATION_CREDENTIALS', 'DATABASE_URL', 'TEST_DATABASE_URL'):
                    env.pop(name)
            forwarded = args.args[1:] if args.args[:1] == ['--'] else args.args
            return subprocess.run([str(NODE), str(OPENCLAW), *forwarded], env=env, cwd=ROOT).returncode
    except KeyboardInterrupt:
        print('Layanan dihentikan; antrean persisten tetap tersimpan.')
        return 130
    except (ProviderUnavailable, ValueError) as exc:
        print(f'GAGAL: {exc}')
        return 1
    except Exception as exc:
        print(f'GAGAL: {type(exc).__name__}; periksa akun/koneksi lokal. Tidak dinyatakan lolos.')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
