"""Fixed, sourced safety copy. Never ask a model to invent emergency contacts."""
import re

SOURCE='https://www.bnpb.go.id/berita/perkembangan-situasi-dan-penanganan-bencana-di-tanah-air-8-oktober-2026'
VERSION='bnpb-safety-2026-11-03'
GENERAL='Utamakan tempat aman. Jangan mendekati api untuk mengambil bukti atau memadamkan api besar seorang diri. Kurangi paparan asap dan ikuti arahan petugas.'


def advice(*,high_risk=False,contact=None):
    text=GENERAL
    if high_risk:
        text+=' Jika jiwa terancam, hubungi layanan darurat resmi secara langsung; bot tidak menjamin petugas sedang menuju lokasi.'
    if (isinstance(contact,dict) and re.fullmatch(r'\+?[0-9]{3,15}',str(contact.get('number','')))
        and str(contact.get('source','')).startswith('https://') and contact.get('verified_at')):
        text+=' Kontak terverifikasi: '+str(contact['number'])+'.'
    return text
