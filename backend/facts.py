"""Sourced text facts. Consent, coordinates and routing are never extracted by AI."""
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


class Quote(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    source_id: str = Field(min_length=1,max_length=100)
    quote: str = Field(min_length=1,max_length=2000)


class Extraction(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    description_sources: list[Quote] = Field(default_factory=list,max_length=20)
    time_sources: list[Quote] = Field(default_factory=list,max_length=5)
    category: Literal['forest_land','building','unknown'] = 'unknown'
    category_source: Quote | None = None


def redact(text):
    text = re.sub(r'https?://\S+|[\w.+-]+@[\w.-]+\.\w+|(?<!\w)(?:\+?62|0)[\d ()-]{8,}\d', '[redaksi]', str(text))
    return ''.join(c for c in text if c in '\n\t' or ord(c)>=32)[:2000]


def validate_extraction(value,sources):
    result=Extraction.model_validate(value).model_dump()
    by_id={str(s['id']):s['text'] for s in sources}
    refs=result['description_sources']+result['time_sources']+([result['category_source']] if result['category_source'] else [])
    for ref in refs:
        if ref['source_id'] not in by_id or ref['quote'] not in by_id[ref['source_id']]:
            raise ValueError('UNSOURCED_FACT')
    if result['category']!='unknown' and not result['category_source']:
        raise ValueError('UNSOURCED_CATEGORY')
    order={str(s['id']):i for i,s in enumerate(sources)}
    result['time_sources'].sort(key=lambda ref:order[ref['source_id']])
    return result


def resolve_time(sources):
    """No date guessing from a bare clock. Relative dates anchor to their source receipt."""
    if not sources:return None
    # Sources are chronological. Resolve the latest explicit date and clock separately,
    # so a clock correction can retain a previously stated date.
    date_source=next((s for s in reversed(sources) if re.search(r'20\d{2}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/20\d{2}|\b(?:hari ini|kemarin)\b',s['text'].lower())),None)
    text=date_source['text'].lower() if date_source else ''
    date=None
    explicit=re.search(r'\b(20\d{2})-(\d{2})-(\d{2})\b',text)
    local=re.search(r'\b(\d{1,2})/(\d{1,2})/(20\d{2})\b',text)
    try:
        if explicit:date=datetime(*map(int,explicit.groups())).date()
        elif local:
            d,m,y=map(int,local.groups());date=datetime(y,m,d).date()
        else:
            for s in reversed(sources):
                if re.search(r'\b(hari ini|kemarin)\b',s['text'].lower()):
                    date=datetime.fromisoformat(s['received_at'].replace('Z','+00:00')).astimezone(ZoneInfo('Asia/Jakarta')).date()
                    if 'kemarin' in s['text'].lower():date-=timedelta(days=1)
                    break
        if date is None:return None
        clock_source=next((s for s in reversed(sources) if re.search(r'\b(?:jam|pukul)\s+',s['text'].lower())),None)
        if not clock_source:return None
        text=clock_source['text'].lower()
        if len(re.findall(r'\b(?:jam|pukul)\s+',text))!=1:return None
        words={'satu':1,'dua':2,'tiga':3,'empat':4,'lima':5,'enam':6,'tujuh':7,'delapan':8,'sembilan':9,'sepuluh':10,'sebelas':11,'dua belas':12}
        clock=re.search(r'\b(?:jam|pukul)\s+(\d{1,2})(?:[.:](\d{2}))?',text)
        if clock:hour=int(clock[1]);minute=int(clock[2] or 0)
        else:
            clock=re.search(r'\b(?:jam|pukul)\s+('+'|'.join(sorted(words,key=len,reverse=True))+r')\b',text)
            if not clock:return None
            hour=words[clock[1]];minute=0
        # A 1..12 clock without day period is ambiguous (except 00 or 13..23).
        period=re.search(r'\b(pagi|siang|sore|malam)\b',text)
        if 1<=hour<=12 and not period:return None
        if period and period[1] in ('siang','sore','malam') and hour<12:hour+=12
        if period and period[1]=='pagi' and hour==12:hour=0
        dt=datetime(date.year,date.month,date.day,hour,minute,tzinfo=ZoneInfo('Asia/Jakarta')).astimezone(timezone.utc)
        received=max(datetime.fromisoformat(s['received_at'].replace('Z','+00:00')) for s in sources)
        return dt.isoformat() if dt<=received+timedelta(minutes=5) else None
    except (ValueError,KeyError,TypeError):return None


def threat_claim(sources):
    patterns=[r'\b(?:ada\s+)?(?:orang|warga|anak|lansia|kami|saya)\s+(?:masih\s+)?(?:terjebak|terkurung|terancam)\b',
              r'\b(?:butuh|perlu|membutuhkan)\s+(?:segera\s+)?evakuasi\b',
              r'\bapi\s+(?:(?:sudah|mulai|sedang)\s+)?(?:mengancam|mendekati|membakar|menjalar ke)\s+(?:rumah|permukiman|pemukiman|sekolah|fasilitas)\b']
    for source in reversed(sources):
        text=source['text'].lower()
        if re.search(r'\b(?:sudah|telah)\s+(?:aman|selesai|padam)\b|\b(?:semua|seluruh)\s+(?:orang|warga|korban)\s+(?:sudah|telah)\s+dievakuasi\b',text):
            return {'level':'unknown','source_id':str(source['id']),'reason':'THREAT_WITHDRAWN_OR_NEEDS_CONFIRMATION'}
        if any(re.search(p,text) for p in patterns):
            if re.search(r'\b(tidak|tak|bukan|belum|jika|kalau|contoh|misal|apakah|kemarin|sudah aman|sudah selesai|sudah dievakuasi)\b',text) or '?' in text:
                return {'level':'unknown','source_id':str(source['id']),'reason':'THREAT_NEEDS_CONFIRMATION'}
            return {'level':'high','source_id':str(source['id']),'quote':source['text'][:1000],'reason':'EXPLICIT_THREAT_CLAIM'}
        if re.search(r'\b(?:tidak|sudah tidak)\s+(?:ada\s+)?(?:ancaman|orang terjebak|bahaya)\b',text):
            return {'level':'unknown','source_id':str(source['id']),'reason':'THREAT_WITHDRAWN'}
    return {'level':'unknown','reason':'NO_EXPLICIT_THREAT'}
