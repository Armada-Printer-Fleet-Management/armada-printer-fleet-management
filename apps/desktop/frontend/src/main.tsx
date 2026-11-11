import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { DesktopRouter } from './DesktopRouter';
import { AgreementGate } from './legal/AgreementGate';
import './index.css';

const root = document.getElementById('root');
if (!root) throw new Error('#root element is missing from index.html');

createRoot(root).render(
  <StrictMode>
    <AgreementGate>
      <DesktopRouter />
    </AgreementGate>
  </StrictMode>,
);
