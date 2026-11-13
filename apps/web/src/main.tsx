import React from 'react';
import { createRoot } from 'react-dom/client';
import { AgreementGate } from './legal/AgreementGate';
import { WebRouter } from './WebRouter';
import './index.css';

const container = document.getElementById('root');
if (!container) throw new Error('Root element not found');
const root = createRoot(container);

root.render(
  <React.StrictMode>
    <AgreementGate>
      <WebRouter />
    </AgreementGate>
  </React.StrictMode>,
);
