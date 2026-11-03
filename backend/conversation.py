"""Deterministic minimum completeness; no authenticity or publication decisions."""

from copy import deepcopy
import re


def new_state():
    return dict(description=None, description_source=None, location=None, location_source=None,
                location_version=0, location_confirmed=False, confirmation_source=None,
                media_ids=[], consent_contact=False, consent_record=None,
                pending_new=False, questions_count=0, status='draft')


def advance(previous, event):
    state = deepcopy(previous)
    state['consent_record'] = None
    text = event.get('text', '').strip()
    command = text.upper()
    changed = False
    if command in ('REPORT', 'LAPOR'):
        state['pending_new'] = True
        return state, 'Masih ada laporan aktif. Ketik LANJUT untuk melengkapinya atau BARU untuk membuat laporan baru. Data lama tetap tersimpan.'
    if command == 'LANJUT':
        state['pending_new'] = False
    if command in ('IZIN KONTAK YA', 'IZIN KONTAK TIDAK'):
        state['consent_contact'] = command.endswith(' YA')
        state['consent_record'] = state['consent_contact']
    if event.get('location'):
        state.update(location=event['location'], location_source=event['id'],
                     location_version=state['location_version'] + 1,
                     location_confirmed=False, confirmation_source=None)
        changed = True
    match = re.fullmatch(r'KONFIRMASI LOKASI ([0-9]+)', command)
    if match and state['location'] and int(match[1]) == state['location_version']:
        if not state['location_confirmed']:
            state.update(location_confirmed=True, confirmation_source=event['id'])
            changed = True
    if command == 'GANTI LOKASI':
        state.update(location=None, location_confirmed=False, confirmation_source=None)
        changed = True
    if command.startswith('KETERANGAN:'):
        description = text.split(':', 1)[1].strip()
        if len(description) >= 10 and description != state['description']:
            state.update(description=description, description_source=event['id'])
            changed = True
    for media in event.get('media', []):
        if media not in state['media_ids']:
            state['media_ids'].append(media)
            changed = True
    if changed:
        state['questions_count'] = 0
    # Ask about an unconfirmed pin first, so a pin is never silently treated as the incident.
    if state['location'] and not state['location_confirmed']:
        missing = ('Apakah titik yang dikirim lokasi kejadian, bukan posisi pelapor? '
                   f"Jika benar ketik KONFIRMASI LOKASI {state['location_version']}; jika salah kirim titik pengganti.")
    elif not state['media_ids']:
        missing = 'Kirim foto atau video kejadian yang dapat dibuka.'
    elif not state['location']:
        missing = 'Kirim pin lokasi kejadian melalui Lampiran > Lokasi; nama tempat saja belum cukup.'
    elif not state['description']:
        missing = 'Kirim KETERANGAN: diikuti penjelasan kejadian (minimal 10 karakter), misalnya apa yang terbakar dan kapan terlihat.'
    else:
        state['status'] = 'complete'
        return state, 'Data minimum lengkap; belum diverifikasi dan belum dipublikasikan. Izin berbagi kontak: ' + ('diberikan.' if state['consent_contact'] else 'tidak diberikan.')
    if state['questions_count'] >= 4:
        state['status'] = 'held'
        return state, 'Draft ditahan karena data belum lengkap. Lengkapi foto/video, pin kejadian dan KETERANGAN: untuk melanjutkan; belum dipublikasikan.'
    state['status'] = 'draft'
    state['questions_count'] += 1
    suffix = (' Opsional: IZIN KONTAK YA atau IZIN KONTAK TIDAK untuk berbagi nomor ke otoritas uji; default tidak dibagikan.'
              if not previous.get('consent_notice_sent') else '')
    state['consent_notice_sent'] = True
    return state, missing + suffix
