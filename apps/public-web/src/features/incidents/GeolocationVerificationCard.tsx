import { useEffect, useRef, useState } from 'react';
import { Icon } from '../../components/ui/Icon';
import { demoLocationOptions, locationCopy, locationSimulationDelay } from '../../mocks/incident';
import type { DemoLocation, LocationState } from './confirmation';
import { showDevelopmentDetails } from '../../app/presentation';

export function GeolocationVerificationCard({ location, onLocationChange }: {
  location: LocationState;
  onLocationChange: (value: LocationState) => void;
}) {
  const [outcome, setOutcome] = useState<DemoLocation>('ready');
  const timer = useRef<number | undefined>(undefined);
  const copy = locationCopy[location];
  const loading = location === 'requesting';

  useEffect(() => () => window.clearTimeout(timer.current), []);

  function activateLocation() {
    window.clearTimeout(timer.current);
    onLocationChange('requesting');
    // Deliberately local: never call browser geolocation or pretend a server replied.
    timer.current = window.setTimeout(() => onLocationChange(outcome), locationSimulationDelay);
  }

  return (
    <section className="panel geolocation-card" aria-labelledby="location-title">
      <div className="section-heading">
        <h2 id="location-title"><Icon name="locate" />Konfirmasi Lokasi Anda</h2>
      </div>
      <p className="section-description">Konfirmasi hanya dapat dikirim dari jarak maksimal 2 km dari titik kejadian.</p>

      <div id="location-status" className={'location-status tone-' + copy.tone} role="status" aria-live="polite" aria-atomic="true">
        <Icon name={loading ? 'loader' : location === 'ready' ? 'checkCircle' : location === 'idle' ? 'locate' : 'info'} size={22} className={loading ? 'spinner' : undefined} />
        <div><strong>{copy.title}</strong><p>{showDevelopmentDetails ? copy.description : 'Pemeriksaan lokasi belum tersedia.'}</p></div>
      </div>
      <button type="button" className={'button button-location w-full' + (showDevelopmentDetails ? '' : ' presentation-action')} onClick={activateLocation} disabled={loading || !showDevelopmentDetails} aria-describedby={showDevelopmentDetails ? 'location-status location-simulation-note' : 'location-status'}>
        <Icon name={loading ? 'loader' : 'locate'} className={loading ? 'spinner' : undefined} />
        {loading ? 'Mengambil Lokasi...' : location === 'idle' ? 'Aktifkan Lokasi' : location === 'ready' ? 'Perbarui Lokasi' : 'Coba Lagi'}
      </button>
      {showDevelopmentDetails && <p id="location-simulation-note" className="simulation-note"><span className="simulation-tag">Simulasi</span>GPS perangkat tidak diakses. Validasi server belum tersedia.</p>}

      {showDevelopmentDetails && <details className="simulation-controls">
        <summary>Pengaturan simulasi lokasi</summary>
        <label htmlFor="demo-location">Kondisi yang ingin dicoba</label>
        <select id="demo-location" value={outcome} onChange={event => {
          window.clearTimeout(timer.current);
          setOutcome(event.target.value as DemoLocation);
          onLocationChange('idle');
        }}>
          {demoLocationOptions.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>
        <p>Pilih kondisi, lalu tekan Aktifkan Lokasi. Hasil hanya demonstrasi tampilan.</p>
      </details>}
    </section>
  );
}
