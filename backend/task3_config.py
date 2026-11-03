"""Private, fail-closed demo routing configuration."""
import hashlib
import json
import re
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]


class Task3Config:
    def __init__(self,path=None):
        self.path=Path(path or ROOT/'.runtime/task3/config.json')

    def read(self):
        try:
            value=json.loads(self.path.read_text(encoding='utf-8'))
            return value if isinstance(value,dict) else {}
        except (OSError,ValueError):return {}

    def region(self):
        cfg=self.read()
        try:
            path=Path(cfg['region_path'])
            raw=path.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=cfg.get('approved_region_sha256'):return None
            return json.loads(raw)
        except (KeyError,OSError,ValueError,TypeError):return None

    def snapshot(self):
        try:return json.loads(Path(self.read()['firms_path']).read_text(encoding='utf-8'))
        except (KeyError,OSError,ValueError,TypeError):return None

    def destinations(self):
        cfg=self.read();dest=cfg.get('destinations',{})
        if cfg.get('distribution_enabled') is not True or not self.region() or not isinstance(dest,dict):return {}
        incoming=cfg.get('inbound_senders')
        if (not isinstance(cfg.get('bot_number'),str) or not re.fullmatch(r'\+[1-9][0-9]{7,14}',cfg['bot_number'])
            or not isinstance(incoming,list) or not incoming or any(not isinstance(n,str) or not re.fullmatch(r'\+[1-9][0-9]{7,14}',n) for n in incoming)):
            return {}
        if set(dest)!= {'community','authority'}:return {}
        numbers=[]
        for role,item in dest.items():
            if not isinstance(item,dict) or not isinstance(item.get('number'),str) or not re.fullmatch(r'\+[1-9][0-9]{7,14}',item['number']) or item.get('account_id')!='default':return {}
            if item['number'] in cfg.get('inbound_senders',[]) or item['number']==cfg.get('bot_number'):return {}
            numbers.append(item['number'])
        return dest if len(set(numbers))==2 else {}

    def allowed(self,role,number,account):
        d=self.destinations().get(role)
        return bool(d and d['number']==number and d['account_id']==account)
