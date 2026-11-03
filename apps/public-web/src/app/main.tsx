import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { IncidentConfirmationPage } from '../pages/IncidentConfirmationPage';
import { LiveIncidentPage } from '../pages/LiveIncidentPage';
import { demoIncident } from '../mocks/incident';
import '@fontsource/inter/latin-400.css';
import '@fontsource/inter/latin-500.css';
import '@fontsource/inter/latin-600.css';
import '@fontsource/inter/latin-700.css';
import '@fontsource/inter/latin-800.css';
import '../styles/app.css';

// A single public demo route needs no router dependency. Unknown slugs stay neutral.
if (import.meta.env.DEV && window.location.pathname === '/') {
  window.history.replaceState(null, '', `/laporan/${demoIncident.slug}`);
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {import.meta.env.DEV && window.location.pathname.includes('/laporan/demo-') ? <IncidentConfirmationPage /> : <LiveIncidentPage />}
  </StrictMode>,
);
