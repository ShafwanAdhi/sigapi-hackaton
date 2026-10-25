import { Icon } from './Icon';
import { demoIncident } from '../../mocks/incident';
import { showDevelopmentDetails } from '../../app/presentation';
import { BrandLogo } from './BrandLogo';
import type { ReactNode } from 'react';

export function SigapiHeader({ children, reference }: { children?: ReactNode; reference?: string }) {
  return (
    <header className="site-header">
      <img
        className="header-photo"
        src="/media/forest-header.webp"
        srcSet="/media/forest-header-960.webp 960w, /media/forest-header-1280.webp 1280w, /media/forest-header-1600.webp 1600w, /media/forest-header.webp 2172w"
        sizes="(max-width: 389px) 1040px, (max-width: 959px) 960px, 100vw"
        width="2172" height="724" alt="" aria-hidden="true" fetchPriority="high" decoding="async"
        onError={event => { event.currentTarget.style.display = 'none'; }}
      />
      <div className="header-inner">
        <a className="brand-link" href={'/laporan/' + demoIncident.slug} aria-label="SIGAPI, halaman laporan"><BrandLogo /></a>
        {reference && <span className="page-label"><span className="sr-only">Nomor laporan: </span>{reference}</span>}
      </div>
      {children}
    </header>
  );
}

export function PageFooter() {
  return (
    <footer className="site-footer">
      <svg className="footer-contours" viewBox="0 0 1600 400" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">
        <defs>
          <pattern id="footer-topography" width="800" height="400" patternUnits="userSpaceOnUse">
            <g fill="none" stroke="currentColor" strokeWidth="1.25">
              <path d="M0 28C120 28 150-32 320-32S650 28 800 28" />
              <path d="M0 68C120 68 150 8 320 8S650 68 800 68" />
              <path d="M0 108C120 108 150 48 320 48S650 108 800 108" />
              <path d="M0 214C140 214 180 144 356 144S660 214 800 214" />
              <path d="M0 254C140 254 180 184 356 184S660 254 800 254" />
              <path d="M0 294C140 294 180 224 356 224S660 294 800 294" />
              <path d="M0 388C120 388 150 328 320 328S650 388 800 388" />
              <path d="M534 110C564 72 662 68 700 108S702 186 646 192 502 160 534 110Z" />
              <path d="M568 122C588 102 644 100 666 122S660 160 632 162 548 148 568 122Z" />
            </g>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#footer-topography)" />
      </svg>
      <div className="footer-inner">
        <div className="footer-brand"><span className="footer-logo"><BrandLogo stacked /></span><strong>Sistem Pelaporan Kebakaran Berbasis Komunitas</strong></div>
        <p>Konfirmasi pengguna merupakan informasi pendukung dan bukan pernyataan resmi dari pihak berwenang.</p>
        {showDevelopmentDetails && <p className="footer-simulation">Prototipe · seluruh data kejadian adalah simulasi.</p>}
      </div>
    </footer>
  );
}

export function SafetyNotice() {
  return <aside className="safety-notice"><Icon name="shield" size={21} /><div><strong>Utamakan keselamatan Anda</strong><p>Jangan mendekati area kebakaran hanya untuk melakukan konfirmasi. Jika situasi membahayakan, hubungi layanan darurat resmi.</p></div></aside>;
}
