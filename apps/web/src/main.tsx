import { ThemeProvider } from '@armada/ui-kit';
import React from 'react';
import { createRoot } from 'react-dom/client';
import { WebRouter } from './WebRouter';
import './index.css';
import { AuthProvider } from './lib/auth-context';
import { setThemePreference, themePreference } from './lib/theme-preference';

const container = document.getElementById('root');
if (!container) throw new Error('Root element not found');
const root = createRoot(container);

root.render(
  <React.StrictMode>
    <ThemeProvider
      initialPreference={themePreference()}
      onPreferenceChange={setThemePreference}
    >
      <AuthProvider>
        <WebRouter />
      </AuthProvider>
    </ThemeProvider>
  </React.StrictMode>,
);
