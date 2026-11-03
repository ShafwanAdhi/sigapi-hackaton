import {createRoot} from 'react-dom/client';
import {StrictMode} from 'react';
import {App} from './App';
import '@fontsource/inter/latin-400.css';
import '@fontsource/inter/latin-500.css';
import '@fontsource/inter/latin-600.css';
import '@fontsource/inter/latin-700.css';
import './style.css';
createRoot(document.getElementById('root')!).render(<StrictMode><App/></StrictMode>);
