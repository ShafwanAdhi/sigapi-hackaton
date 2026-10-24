import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { IncidentConfirmationPage } from '../pages/IncidentConfirmationPage';
import { demoIncident } from '../mocks/incident';
import '../styles/app.css';

// A single public demo route needs no router dependency. Unknown slugs stay neutral.
if (window.location.pathname === '/') {
  window.history.replaceState(null, '', `/laporan/${demoIncident.slug}`);
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <IncidentConfirmationPage />
  </StrictMode>,
);
