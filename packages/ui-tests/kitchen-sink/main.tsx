import { isThemePreference, ThemeProvider } from '@armada/ui-kit';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import { KitchenSink } from './KitchenSink';
import './kitchen-sink.css';

// Tests choose the starting theme and an optional dialog through the URL, so each test opens
// the kitchen sink already in the state it checks.
const params = new URLSearchParams(window.location.search);
const theme = params.get('theme');

const container = document.getElementById('root');
if (!container) throw new Error('Root element not found');

createRoot(container).render(
  <StrictMode>
    <ThemeProvider
      initialPreference={isThemePreference(theme) ? theme : 'system'}
    >
      <KitchenSink dialog={params.get('dialog')} />
    </ThemeProvider>
  </StrictMode>,
);
