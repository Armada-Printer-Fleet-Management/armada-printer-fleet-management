import { type ThemePreference, ThemeProvider } from '@armada/ui-kit';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { DesktopRouter } from './DesktopRouter';
import { AgreementGate } from './legal/AgreementGate';
import { setThemePreference, themePreference } from './lib/theme-preference';
import './index.css';

const root = document.getElementById('root');
if (!root) throw new Error('#root element is missing from index.html');

const render = (initialPreference: ThemePreference) => {
  createRoot(root).render(
    <StrictMode>
      <ThemeProvider
        initialPreference={initialPreference}
        onPreferenceChange={setThemePreference}
      >
        <AgreementGate>
          <DesktopRouter />
        </AgreementGate>
      </ThemeProvider>
    </StrictMode>,
  );
};

// Read before the first render, so the app never paints in the wrong theme. Until then the page
// follows the OS.
void themePreference().then(render);
