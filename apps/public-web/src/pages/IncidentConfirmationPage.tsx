import { SigapiHeader, PageFooter, SafetyNotice } from '../components/ui/PageShell';
import { IncidentInformationCard } from '../features/incidents/IncidentInformationCard';
import { IncidentMap } from '../features/incidents/IncidentMap';
import { ConfirmationForm } from '../features/incidents/ConfirmationForm';
import { demoIncident } from '../mocks/incident';
import { showDevelopmentDetails } from '../app/presentation';

export function IncidentConfirmationPage() {
  const slug = window.location.pathname.replace(/\/$/, '').split('/')[2];
  const exists = window.location.pathname.startsWith('/laporan/') && window.location.pathname.replace(/\/$/, '').split('/').length === 3 && (slug === demoIncident.slug || slug === demoIncident.legacySlug);

  return (
    <>
      <a className="skip-link" href="#main">Lewati ke konten utama</a>
      <SigapiHeader reference={exists ? demoIncident.publicReference : undefined}>
        {exists && (
          <div className="page-intro">
            <div className="intro-labels"><span className="intro-eyebrow">KONFIRMASI PUBLIK</span>{showDevelopmentDetails && <span className="simulation-tag">Data simulasi</span>}</div>
            <h1>Konfirmasi Laporan Kebakaran</h1>
            <p>Periksa foto dan lokasi kejadian, lalu konfirmasikan kondisi yang Anda lihat.</p>
          </div>
        )}
      </SigapiHeader>
      <main id="main" className="page-shell">
        {!exists ? <section className="panel not-found"><h1>Laporan tidak tersedia.</h1><p>Periksa kembali tautan yang Anda terima.</p><a className="button button-location" href={'/laporan/' + demoIncident.slug}>Kembali ke laporan</a></section> : <>
          <div className="content-stack">
            <div className="incident-context">
              <IncidentInformationCard />
              <IncidentMap />
            </div>
            <ConfirmationForm />
            <SafetyNotice />
          </div>
        </>}
      </main>
      <PageFooter />
    </>
  );
}
