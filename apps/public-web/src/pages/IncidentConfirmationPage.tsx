import { useState } from 'react';
import { Icon } from '../components/ui/Icon';
import { ConfirmationForm } from '../features/incidents/ConfirmationForm';
import { IncidentMap } from '../features/incidents/IncidentMap';
import { demoIncident } from '../mocks/incident';

const reportedTime = new Intl.DateTimeFormat('id-ID', {
  day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Jakarta',
}).format(new Date(demoIncident.reportedAt));

export function IncidentConfirmationPage() {
  const [photoUnavailable, setPhotoUnavailable] = useState(false);
  const exists = window.location.pathname === `/laporan/${demoIncident.slug}` || window.location.pathname === `/laporan/${demoIncident.slug}/`;

  return (
    <>
      <a className="skip-link" href="#main">Lewati ke konten utama</a>
      <header className="site-header">
        <div className="header-inner">
          <a className="wordmark" href={`/laporan/${demoIncident.slug}`} aria-label="SIGAPI, halaman demo">SIGAPI<span>.</span></a>
          <span className="header-purpose"><Icon name="shield" size={17} /> Konfirmasi publik</span>
        </div>
      </header>
      <main id="main" className="page-shell">
        {!exists ? <section className="not-found panel"><span className="eyebrow">SIGAPI</span><h1>Laporan tidak tersedia.</h1><p>Periksa kembali tautan yang Anda terima.</p><a className="button button-secondary" href={`/laporan/${demoIncident.slug}`}>Buka contoh simulasi <Icon name="arrow" /></a></section> : <>
          <div className="page-intro">
            <div className="intro-meta"><span className="eyebrow">INFORMASI & KONFIRMASI KEJADIAN</span><span className="demo-badge">Data simulasi</span></div>
            <h1>{demoIncident.title}</h1>
            <p>Lihat informasi kejadian dan bantu konfirmasi kondisi di sekitar Anda.</p>
          </div>

          <div className="content-grid">
            <section className="incident-panel panel" aria-labelledby="incident-title">
              <div className="section-kicker"><span className="section-number">01</span> INFORMASI KEJADIAN</div>
              <div className="incident-meta"><span className="reference">{demoIncident.publicReference}</span><span className="status-badge"><span />Laporan awal</span></div>
              <h2 id="incident-title">{demoIncident.category}</h2>

              <dl className="incident-details">
                <div><Icon name="pin" /><div><dt>Lokasi yang dilaporkan</dt><dd>{demoIncident.location}<small>{demoIncident.locationDetail}</small></dd></div></div>
                <div><Icon name="clock" /><div><dt>Waktu dilaporkan</dt><dd><time dateTime={demoIncident.reportedAt}>{reportedTime} WIB</time></dd></div></div>
              </dl>

              <div className="report-summary"><h3>Ringkasan laporan awal</h3><p>{demoIncident.summary}</p><span>Skenario sintetis · bukan laporan warga sesungguhnya.</span></div>

              <figure className="incident-photo">
                {photoUnavailable ? <div className="image-fallback"><Icon name="image" size={32} /><span>Ilustrasi simulasi tidak tersedia.</span></div> : <img src={demoIncident.photoUrl} alt={demoIncident.photoAlt} width={1200} height={800} onError={() => setPhotoUnavailable(true)} />}
                <figcaption><Icon name="image" size={14} />Ilustrasi AI · bukan foto kejadian nyata</figcaption>
              </figure>

              <div className="map-heading"><h3>Lokasi kejadian</h3><span className="mini-tag">Simulasi</span></div>
              <IncidentMap />

              <div className="public-summary"><Icon name="info" size={19} /><div><strong>Belum ada konfirmasi lapangan</strong><p>Kondisi terkini dan penanganan belum dikonfirmasi.</p></div></div>
              <a href="#konfirmasi" className="button button-primary overview-action" onClick={() => document.getElementById('konfirmasi')?.focus({ preventScroll: true })}>Berikan konfirmasi<Icon name="arrow" /></a>
            </section>

            <ConfirmationForm />
          </div>

          <aside className="emergency-note"><Icon name="info" size={19} /><p>Jika situasi membahayakan keselamatan, hubungi layanan darurat resmi. SIGAPI bukan layanan respons darurat langsung.</p></aside>
        </>}
      </main>
      <footer className="site-footer"><span>SIGAPI · Informasi yang membantu, dari sekitar Anda.</span><span>Prototipe · seluruh data kejadian adalah simulasi.</span></footer>
    </>
  );
}
