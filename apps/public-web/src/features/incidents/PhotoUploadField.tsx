import { useEffect, useRef, useState } from 'react';
import type { ChangeEvent } from 'react';
import { Icon } from '../../components/ui/Icon';

export function PhotoUploadField() {
  const [photo, setPhoto] = useState<{ file: File; url: string } | null>(null);
  const [error, setError] = useState('');
  const [decoding, setDecoding] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const chooseButton = useRef<HTMLButtonElement>(null);
  const photoRequest = useRef(0);

  useEffect(() => () => { if (photo) URL.revokeObjectURL(photo.url); }, [photo]);
  useEffect(() => () => { photoRequest.current += 1; }, []);

  function removePhoto() {
    photoRequest.current += 1;
    setPhoto(null);
    setError('');
    setDecoding(false);
    if (fileInput.current) fileInput.current.value = '';
    window.requestAnimationFrame(() => chooseButton.current?.focus());
  }

  async function choosePhoto(event: ChangeEvent<HTMLInputElement>) {
    const request = ++photoRequest.current;
    const file = event.target.files?.[0];
    if (!file) return;
    setPhoto(null);
    setError('');
    setDecoding(false);
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 10 * 1024 * 1024) {
      setError('Pilih foto JPG, PNG, atau WebP dengan ukuran maksimal 10 MB.');
      event.target.value = '';
      return;
    }
    setDecoding(true);
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
        setError('Foto tidak dapat dibuka. Silakan pilih berkas foto lain.');
        if (fileInput.current) fileInput.current.value = '';
      }
    } finally {
      if (request === photoRequest.current) setDecoding(false);
    }
  }

  return (
    <div className="form-field photo-field">
      <label htmlFor="photo">Tambahkan Foto <span className="optional">(opsional)</span></label>
      <input className="sr-only" tabIndex={-1} ref={fileInput} id="photo" type="file" accept="image/jpeg,image/png,image/webp" onChange={choosePhoto} aria-describedby={error ? 'photo-error photo-note' : 'photo-note'} aria-invalid={Boolean(error)} />
      {photo ? <figure className="photo-preview">
        <img src={photo.url} alt="Preview foto kondisi lapangan yang Anda pilih" />
        <figcaption><span title={photo.file.name}>{photo.file.name}</span><button type="button" className="remove-photo" onClick={removePhoto}><Icon name="cross" size={16} />Hapus foto</button></figcaption>
      </figure> : <button ref={chooseButton} type="button" className="upload-zone" onClick={() => fileInput.current?.click()} disabled={decoding} aria-describedby={error ? 'photo-error photo-note' : 'photo-note'}>
        <span className="upload-icon"><Icon name={decoding ? 'loader' : 'imagePlus'} size={24} className={decoding ? 'spinner' : undefined} /></span>
        <strong>{decoding ? 'Membaca foto...' : 'Pilih foto dari perangkat'}</strong>
        <span>JPG, PNG, atau WebP · maksimal 10 MB</span>
      </button>}
      {error && <p id="photo-error" className="field-error" role="alert"><Icon name="info" size={16} />{error}</p>}
      <p id="photo-note" className="field-hint">Tambahkan foto kondisi yang Anda amati dari tempat aman.</p>
    </div>
  );
}
