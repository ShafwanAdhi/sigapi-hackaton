"""Local operator commands for Task 1. Secrets remain in .env/ADC."""

import argparse
import json
import os
import re
import secrets
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

from backend.providers import ProviderUnavailable, groq_observe, web_detect
from backend.smoke import VisionBudget

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
                       'GROQ_API_KEY=\nGROQ_VISION_MODEL=\nGOOGLE_CLOUD_PROJECT=\n')
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
        'GROQ_VISION_MODEL', 'GOOGLE_CLOUD_PROJECT']}
    try:
        import google.auth
        google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
        status['google_adc_found'] = True
    except Exception:
        status['google_adc_found'] = False
    status.update(node_local=NODE.exists(), openclaw_installed=OPENCLAW.exists(),
                  openclaw_config=CONFIG.exists(), ffmpeg=bool(shutil.which('ffmpeg')),
                  ffprobe=bool(shutil.which('ffprobe')))
    print(json.dumps(status, indent=2))
    return 0 if all(status.values()) else 1


def provider_smoke(args):
    from backend.media import sample_media
    frames = sample_media(Path(args.image))
    run = {'checked_at': datetime.now(timezone.utc).isoformat(), 'test_case': args.case,
           'mode': 'live_provider_smoke', 'groq_model': os.environ.get('GROQ_VISION_MODEL'),
           'frames': [], 'limitations': 'Observasi terbatas pada gambar/frame; bukan bukti keaslian atau keputusan publikasi.'}
    budget = VisionBudget(RUNTIME / 'vision-budget.sqlite3')
    # Ordinary operator environment controls proxy/TLS; never disable certificate verification.
    with httpx.Client() as client:
        for data in frames:
            frame = {}
            if args.provider in ('groq', 'both'):
                frame['groq'] = groq_observe(data, client, os.environ.get('GROQ_API_KEY'), os.environ.get('GROQ_VISION_MODEL'))
            if args.provider in ('vision', 'both'):
                import google.auth
                from google.auth.transport.requests import Request
                project = os.environ.get('GOOGLE_CLOUD_PROJECT')
                if not project:
                    raise ValueError('GOOGLE_CLOUD_PROJECT belum diisi')
                credentials, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'], quota_project_id=project)
                credentials.refresh(Request())
                frame['vision'] = web_detect(data, client, budget, {
                    'Authorization': f'Bearer {credentials.token}', 'x-goog-user-project': project})
            run['frames'].append(frame)
    RUNTIME.mkdir(exist_ok=True)
    output = RUNTIME / f'smoke-{secrets.token_hex(8)}.json'
    output.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Hasil nyata tersimpan lokal: {output}')


def main():
    load_dotenv(ROOT / '.env', interpolate=False)
    parser = argparse.ArgumentParser(description='SIGAPI Task 1; belum sistem laporan produksi')
    commands = parser.add_subparsers(dest='command', required=True)
    config = commands.add_parser('configure')
    config.add_argument('--team-number', required=True)
    commands.add_parser('readiness')
    commands.add_parser('serve')
    smoke = commands.add_parser('providers')
    smoke.add_argument('--image', required=True, help='Foto/video berizin di disk lokal')
    smoke.add_argument('--case', required=True, choices=['fire', 'no_fire', 'blurred', 'web_known', 'video'])
    smoke.add_argument('--provider', choices=['groq', 'vision', 'both'], default='both')
    claw = commands.add_parser('openclaw')
    claw.add_argument('args', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        if args.command == 'configure':
            configure(args.team_number)
        elif args.command == 'readiness':
            return readiness()
        elif args.command == 'providers':
            provider_smoke(args)
        elif args.command == 'serve':
            import uvicorn
            from backend.internal import create_app
            uvicorn.run(create_app(), host='127.0.0.1', port=8011, access_log=False)
        elif args.command == 'openclaw':
            if not NODE.exists() or not OPENCLAW.exists():
                raise ValueError('OpenClaw/Node lokal belum terpasang lengkap')
            env = dict(os.environ, OPENCLAW_STATE_DIR=str(CONFIG.parent), OPENCLAW_CONFIG_PATH=str(CONFIG),
                       PATH=str(NODE.parent) + os.pathsep + os.environ['PATH'])
            # Transport process does not need provider credentials.
            for name in list(env):
                if name.endswith('_API_KEY') or name == 'GOOGLE_APPLICATION_CREDENTIALS':
                    env.pop(name)
            forwarded = args.args[1:] if args.args[:1] == ['--'] else args.args
            return subprocess.run([str(NODE), str(OPENCLAW), *forwarded], env=env, cwd=ROOT).returncode
    except (ProviderUnavailable, ValueError) as exc:
        print(f'GAGAL: {exc}')
        return 1
    except Exception as exc:
        print(f'GAGAL: {type(exc).__name__}; periksa akun/koneksi lokal. Tidak dinyatakan lolos.')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
