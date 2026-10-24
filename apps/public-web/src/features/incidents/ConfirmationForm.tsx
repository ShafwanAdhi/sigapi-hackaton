import { useEffect, useReducer, useRef, useState } from 'react';
import type { ChangeEvent, FormEvent } from 'react';
import { Icon } from '../../components/ui/Icon';
import { canPreview, confirmationReducer, initialConfirmation, locationCopy } from './confirmation';
import type { DemoLocation } from './confirmation';

export function ConfirmationForm() {
  const [state, dispatch] = useReducer(confirmationReducer, initialConfirmation);
  const [demoLocation, setDemoLocation] = useState<DemoLocation>('ready');
  const [photo, setPhoto] = useState<{ file: File; url: string } | null>(null);
  const [photoError, setPhotoError] = useState('');
  const fileInput = useRef<HTMLInputElement>(null);
  const photoRequest = useRef(0);
  const resultRef = useRef<HTMLDivElement>(null);
  const copy = locationCopy[state.location];
  const eligible = canPreview(state);

  useEffect(() => () => { if (photo) URL.revokeObjectURL(photo.url); }, [photo]);
  useEffect(() => { if (state.previewed) resultRef.current?.focus(); }, [state.previewed]);

  function removePhoto() {
    photoRequest.current += 1;
    setPhoto(null);
    setPhotoError('');
    if (fileInput.current) fileInput.current.value = '';
    dispatch({ type: 'edited' });
  }

  async function choosePhoto(event: ChangeEvent<HTMLInputElement>) {
    const request = ++photoRequest.current;
    const file = event.target.files?.[0];
    setPhoto(null);
    setPhotoError('');
    dispatch({ type: 'edited' });
    if (!file) return;
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 10 * 1024 * 1024) {
      setPhotoError('Pilih foto JPG, PNG, atau WebP dengan ukuran maksimal 10 MB.');
      event.target.value = '';
      return;
    }
    const url = URL.createObjectURL(file);
    const image = new Image();
    image.src = url;
    try {
      await image.decode();
      if (request !== photoRequest.current) { URL.revokeObjectURL(url); return; }
      setPhoto({ file, url });
    } catch {
      URL.revokeObjectURL(url);
      if (request === photoRequest.current) {
        setPhotoError('Foto tidak dapat dibuka. Silakan pilih berkas foto lain.');
        if (fileInput.current) fileInput.current.value = '';
      }
    }
  }

  function submitPreview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (eligible) dispatch({ type: 'preview' });
  }

  return (
    <section id="konfirmasi" className="confirmation-panel panel" aria-labelledby="confirmation-title" tabIndex={-1}>
      <div className="section-kicker"><span className="section-number">02</span> KONFIRMASI LAPANGAN</div>
      <h2 id="confirmation-title">Bantu lengkapi laporan ini.</h2>
      <p className="section-description">Bagikan kondisi yang Anda amati dari tempat aman.</p>

      <form onSubmit={submitPreview}>
        <section className="location-block" aria-labelledby="location-title">
          <div className="flex items-center gap-2"><Icon name="locate" /><h3 id="location-title">Periksa lokasi Anda</h3><span className="mini-tag">Simulasi</span></div>
          <p className="field-hint">Konfirmasi hanya dapat dikirim dalam radius 2 km. Lokasi Anda tidak ditampilkan kepada publik.</p>
          <div className="demo-control">
            <label htmlFor="demo-location">Coba kondisi lokasi</label>
            <select id="demo-location" value={demoLocation} onChange={event => {
              setDemoLocation(event.target.value as DemoLocation);
              dispatch({ type: 'location', value: 'idle' });
            }}>
              <option value="ready">Dalam radius · 850 m</option>
              <option value="denied">Izin lokasi ditolak</option>
              <option value="outside">Di luar radius · 2,8 km</option>
            </select>
            <p>Kontrol demo · tidak mengakses GPS perangkat.</p>
          </div>
          <button type="button" className="button button-secondary w-full" onClick={() => dispatch({ type: 'location', value: demoLocation })}>
            <Icon name="locate" />{state.location === 'idle' ? 'Coba lokasi simulasi' : 'Ulangi simulasi lokasi'}
          </button>
          <div className={`location-status ${state.location}`} role="status" aria-live="polite" aria-atomic="true">
            <Icon name={state.location === 'ready' ? 'check' : 'info'} size={18} />
            <div><strong>{copy.title}</strong><p>{copy.description}</p></div>
          </div>
        </section>

        <fieldset className="choice-fieldset">
          <legend>Apakah kejadian ini benar terjadi?<span className="required-label">Wajib dipilih</span></legend>
          <label className={`choice-card ${state.choice === 'valid' ? 'selected' : ''}`}>
            <input type="radio" name="choice" value="valid" checked={state.choice === 'valid'} onChange={() => dispatch({ type: 'choice', value: 'valid' })} required />
            <span className="choice-icon"><Icon name="check" size={19} /></span>
            <span><strong>Ya, benar terjadi</strong><small>Kondisi sesuai dengan laporan.</small></span>
          </label>
          <label className={`choice-card ${state.choice === 'invalid' ? 'selected' : ''}`}>
            <input type="radio" name="choice" value="invalid" checked={state.choice === 'invalid'} onChange={() => dispatch({ type: 'choice', value: 'invalid' })} />
            <span className="choice-icon"><Icon name="cross" size={19} /></span>
            <span><strong>Tidak, kondisi tidak sesuai</strong><small>Pengamatan saya berbeda dari laporan.</small></span>
          </label>
          {state.choice === 'valid' && <div className="solved-block">
            <label className="checkbox-label"><input type="checkbox" checked={state.solved} onChange={event => dispatch({ type: 'solved', value: event.target.checked })} /><span>Berdasarkan pengamatan saya, kebakaran sudah tertangani <span className="optional">(opsional)</span></span></label>
            <p className="field-hint">Pernyataan pengguna, bukan konfirmasi resmi BPBD.</p>
          </div>}
        </fieldset>

        <div className="form-field">
          <label htmlFor="description">Keterangan tambahan <span className="optional">(opsional)</span></label>
          <textarea id="description" rows={4} maxLength={2000} placeholder="Ceritakan kondisi yang Anda lihat dari tempat aman…" value={state.description} onChange={event => dispatch({ type: 'description', value: event.target.value })} aria-describedby="description-count" />
          <span id="description-count" className="character-count">{state.description.length.toLocaleString('id-ID')} / 2.000 karakter</span>
        </div>

        <div className="form-field photo-field">
          <label htmlFor="photo">Foto kondisi lapangan <span className="optional">(opsional)</span></label>
          <div className="upload-zone">
            <Icon name="upload" size={23} />
            <span>Tambahkan foto pengamatan Anda</span>
            <small>JPG, PNG, atau WebP · maksimal 10 MB</small>
            <button type="button" className="button button-secondary upload-button" onClick={() => fileInput.current?.click()}>Pilih foto</button>
            <input className="sr-only" tabIndex={-1} ref={fileInput} id="photo" type="file" accept="image/jpeg,image/png,image/webp" onChange={choosePhoto} aria-describedby={photoError ? 'photo-error photo-note' : 'photo-note'} aria-invalid={Boolean(photoError)} />
          </div>
          {photoError && <p id="photo-error" className="field-error" role="alert">{photoError}</p>}
          {photo && <figure className="photo-preview">
            <img src={photo.url} alt="Preview foto kondisi lapangan yang Anda pilih" />
            <figcaption><span>{photo.file.name}</span><button type="button" onClick={removePhoto} className="text-button">Hapus foto</button></figcaption>
          </figure>}
          <p id="photo-note" className="field-hint">Preview hanya di perangkat ini. Foto tidak diunggah.</p>
        </div>

        <div className="safety-note"><Icon name="shield" size={19} /><p>Utamakan keselamatan. Jangan mendekati api untuk mengambil foto atau memenuhi radius konfirmasi.</p></div>
        <button className="button button-primary w-full" type="submit" disabled={!eligible || Boolean(photoError)}><span>Coba kirim konfirmasi</span><Icon name="arrow" size={19} /></button>
        <p className="submit-hint">{!state.choice ? 'Pilih jawaban dan coba lokasi simulasi untuk melanjutkan.' : state.location !== 'ready' ? 'Gunakan simulasi lokasi dalam radius untuk melanjutkan.' : 'Siap dicoba dalam mode simulasi.'}</p>
        <p className="prototype-note">Demo tampilan · jawaban tidak disimpan atau dikirim ke pihak mana pun.</p>

        {state.previewed && <div ref={resultRef} className="preview-result" role="status" tabIndex={-1}>
          <div className="flex items-center gap-2"><Icon name="info" /><strong>Simulasi selesai · belum dikirim</strong></div>
          <p>Ini hanya preview interaksi. Tidak ada konfirmasi yang disimpan.</p>
          <dl><div><dt>Pilihan</dt><dd>{state.choice === 'valid' ? 'Kejadian benar terjadi' : 'Kondisi tidak sesuai'}</dd></div><div><dt>Klaim selesai</dt><dd>{state.solved ? 'Dicentang (klaim pengguna)' : 'Tidak dicentang'}</dd></div><div><dt>Foto</dt><dd>{photo ? 'Ada preview lokal' : 'Tidak ditambahkan'}</dd></div></dl>
        </div>}
      </form>
    </section>
  );
}
