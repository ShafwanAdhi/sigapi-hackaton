import { useState } from 'react';
import { Icon } from '../../components/ui/Icon';
import { demoIncident } from '../../mocks/incident';
import { showDevelopmentDetails } from '../../app/presentation';

export function IncidentInformationCard() {
  const [photoUnavailable, setPhotoUnavailable] = useState(false);
  return (
    <section className="panel incident-card" aria-labelledby="incident-title">
      <div className="section-heading incident-heading">
        <h2 id="incident-title">Informasi Kejadian</h2>
        <span className="status-badge"><Icon name="warning" size={16} />{demoIncident.status}</span>
      </div>
      <figure className="incident-photo">
        {photoUnavailable
          ? <div className="image-fallback"><Icon name="image" size={32} /><p>Dokumentasi belum tersedia untuk publik.</p></div>
          : <img src={demoIncident.photoUrl} alt={demoIncident.photoAlt} width={1200} height={800} onError={() => setPhotoUnavailable(true)} />}
        {showDevelopmentDetails && <figcaption><Icon name="image" size={14} />Ilustrasi AI · data simulasi</figcaption>}
      </figure>
      <h3 className="incident-name">{demoIncident.title}</h3>
      <div className="incident-details">
        <p><Icon name="pin" /><span>{demoIncident.location}</span></p>
        <p><Icon name="calendar" /><span>{demoIncident.timeLabel}</span></p>
      </div>
    </section>
  );
}
