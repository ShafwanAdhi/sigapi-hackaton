"""Cross-platform entrypoints. Runtime credentials stay in environment or stdin."""
import argparse
import getpass
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from backend.mvp_store import MvpStore


def main():
    load_dotenv(interpolate=False)
    parser=argparse.ArgumentParser(description='SIGAPI application operations')
    commands=parser.add_subparsers(dest='command',required=True)
    for name in ('migrate','internal','web','intake-worker','analysis-worker','scheduler','status'):
        commands.add_parser(name)
    admin=commands.add_parser('admin-create');admin.add_argument('--username',required=True)
    admin.add_argument('--region',default='35.73');admin.add_argument('--password-stdin',action='store_true')
    region=commands.add_parser('import-region');region.add_argument('--file',required=True)
    region.add_argument('--approve',action='store_true');region.add_argument('--reason',required=True)
    setting=commands.add_parser('settings');setting.add_argument('--json',required=True)
    health=commands.add_parser('health');health.add_argument('--service',required=True,choices=['intake','analysis','scheduler','gateway'])
    purge=commands.add_parser('purge');purge.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    store=MvpStore(os.environ.get('DATABASE_URL'))
    data=Path(os.environ.get('SIGAPI_DATA_DIR','.runtime/mvp')).resolve()
    media=data/'media';media.mkdir(parents=True,exist_ok=True)
    if args.command=='migrate':store.migrate();print('Database migrations applied.');return
    if args.command=='admin-create':
        password=sys.stdin.readline().rstrip('\r\n') if args.password_stdin else getpass.getpass('Admin password (min 14 chars): ')
        store.create_admin(args.username,password,args.region);print('Admin account provisioned.');return
    if args.command=='import-region':
        if len(args.reason.strip())<10:raise ValueError('REVIEW_REASON_REQUIRED')
        feature=json.loads(Path(args.file).read_text(encoding='utf-8'))
        digest=store.set_region(feature,approve=args.approve)
        with store.connect() as db:store.audit(db,None,'REGION_REVIEW',{'reason':args.reason,'sha256':digest,'approved':args.approve},'system_cli')
        print(json.dumps({'sha256':digest,'approved':args.approve}));return
    if args.command=='settings':
        changes=json.loads(args.json)
        if not isinstance(changes,dict) or set(changes)-{'distribution_enabled','public_intake','live_gate_passed','emergency_contact'}:
            raise ValueError('INVALID_SETTINGS')
        store.set_settings(changes);print('Service settings saved.');return
    if args.command=='purge':
        from backend.maintenance import purge
        print(json.dumps(purge(store,media,dry_run=not args.apply,gateway_root=os.environ.get('SIGAPI_GATEWAY_DATA_DIR'))));return
    if args.command=='status':
        with store.connect() as db:
            heartbeats=db.execute("SELECT service,last_seen,details,last_seen>now()-interval '90 seconds' AS recent FROM service_heartbeats ORDER BY service").fetchall()
            destinations=db.execute("SELECT role,count(*) n FROM destinations WHERE region_code='35.73' AND active AND authorized GROUP BY role").fetchall()
        by_role={row['role']:row['n'] for row in destinations}
        cfg=store.config.read();recent={row['service']:bool(row['recent']) for row in heartbeats}
        print(json.dumps({'heartbeats':heartbeats,'region_approved':bool(store.region()),
            'firms_current':bool(store.snapshot()),'community_destination':'ready' if by_role.get('community') else 'missing',
            'authority_destination':'ready' if by_role.get('authority') else 'missing',
            'gateway_heartbeat':'ready' if recent.get('gateway') else 'unknown',
            'provider_configured':bool(os.environ.get('GROQ_API_KEY') and os.environ.get('GROQ_VISION_MODEL')),
            'distribution_enabled':bool(cfg.get('distribution_enabled')),'public_intake':bool(cfg.get('public_intake')),
            'live_gate':'passed' if cfg.get('live_gate_passed') else 'pending','settings':cfg},default=str));return
    if args.command=='health':
        with store.connect() as db:
            row=db.execute("SELECT 1 FROM service_heartbeats WHERE service=%s AND last_seen>now()-interval '90 seconds'",(args.service,)).fetchone()
        sys.exit(0 if row else 1)
    if args.command in ('internal','web'):
        import uvicorn
        if args.command=='internal':
            from backend.intake_api import create_intake_app
            app=create_intake_app(os.environ.get('INTERNAL_API_TOKEN'),store,media);port=8011
        else:
            from backend.web_api import create_web_app
            app=create_web_app(store,media,secure_cookies=os.environ.get('SIGAPI_INSECURE_LOCAL_COOKIE')!='true');port=8012
        uvicorn.run(app,host=os.environ.get('SIGAPI_BIND','127.0.0.1'),port=port,access_log=False,
                    proxy_headers=True,forwarded_allow_ips=os.environ.get('SIGAPI_TRUSTED_PROXIES','127.0.0.1'),
                    limit_concurrency=4 if args.command=='web' else 8,ws='none')
    elif args.command=='intake-worker':
        from backend.worker import run_worker
        run_worker(store,media)
    elif args.command=='analysis-worker':
        from backend.analysis_engine import AnalysisEngine,run_analysis_worker
        run_analysis_worker(AnalysisEngine(store,media,store.config))
    elif args.command=='scheduler':
        from backend.maintenance import run_scheduler
        run_scheduler(store,media,retention=os.environ.get('SIGAPI_RETENTION_ENABLED')=='true',gateway_root=os.environ.get('SIGAPI_GATEWAY_DATA_DIR'))


if __name__=='__main__':
    main()
