import { Icon } from '../../components/ui/Icon';
import { showDevelopmentDetails } from '../../app/presentation';

export function IncidentMap() {
  return (
    <section className="panel incident-location-card" aria-labelledby="map-heading">
      <div className="section-heading">
        <h2 id="map-heading"><Icon name="map" />Lokasi Kejadian</h2>
        {showDevelopmentDetails && <span className="simulation-tag">Simulasi</span>}
      </div>
      <p className="section-description">Titik pada peta menunjukkan lokasi kejadian yang dilaporkan.</p>
      <figure className="map-figure">
        <div className="map-canvas">
          <svg viewBox="0 0 640 220" preserveAspectRatio="xMidYMid slice" role="img" aria-labelledby="map-title map-description">
            <title id="map-title">Lokasi kejadian di Kota Malang</title>
            <desc id="map-description">Titik lokasi kejadian berbeda dengan lokasi pengguna yang memberikan konfirmasi.</desc>
            <rect width="640" height="220" fill="var(--color-map-ground)" />
            <path d="M0 0h192l-38 81H0ZM460 0h180v60l-143 22ZM0 151l172-15 43 84H0ZM432 163l208-32v89H460Z" fill="var(--color-map-block)" />
            <path d="M523-20c-44 63-76 58-42 110s-31 67-12 150" fill="none" stroke="var(--color-map-water)" strokeWidth="16" />
            <g fill="none" stroke="var(--color-surface)" strokeWidth="12"><path d="m-20 103 680-30M220-20l39 260M-20 207 680-237M-20 14l680 185" /></g>
            <g fill="none" stroke="var(--color-surface)" strokeWidth="5"><path d="m80-10 48 250M369-10l-14 250M594-10l-40 250M0 150l640-35" /></g>
            <circle cx="320" cy="110" r="44" fill="var(--color-primary)" fillOpacity=".1" stroke="var(--color-primary)" strokeDasharray="4 5" />
            <circle cx="320" cy="110" r="22" fill="var(--color-surface)" />
            <g transform="translate(302 89)" color="var(--color-primary)">
              <Icon name="pin" size={36} />
            </g>
          </svg>
          <span className="map-caption">Kota Malang, Jawa Timur</span>
          <span className="map-pin-label">Titik kejadian</span>
        </div>
        <figcaption>Lokasi kejadian berbeda dengan lokasi Anda. Peta ini bukan alat navigasi.</figcaption>
      </figure>
    </section>
  );
}
