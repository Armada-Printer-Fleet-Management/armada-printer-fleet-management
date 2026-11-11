import { lazy, Suspense } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router';

import { AppLayout } from './components/AppLayout';
import { AgreementGate } from './legal/AgreementGate';
import { HelpPage } from './pages/HelpPage';
import { HomePage } from './pages/HomePage';
import { MyPrintsPage } from './pages/MyPrintsPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { TrainingPage } from './pages/TrainingPage';
import { routePaths } from './routes';
import { SignInCallbackPage } from './pages/SignInCallbackPage';

// Written as a literal DEV check so Vite removes the import, and with it the dev tools code,
// from the production bundle.
const TempPage = import.meta.env.DEV
  ? lazy(() =>
      import('./pages/TempPage').then((m) => ({ default: m.TempPage })),
    )
  : null;

export function WebRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path={routePaths.signInCallback.path}
          element={<SignInCallbackPage />}
        />
        {/* The sign-in callback above is never gated, so signing in always completes. */}
        <Route
          element={
            <AgreementGate>
              <AppLayout />
            </AgreementGate>
          }
        >
          <Route index element={<HomePage />} />
          <Route path={routePaths.myPrints.path} element={<MyPrintsPage />} />
          <Route path={routePaths.training.path} element={<TrainingPage />} />
          <Route path={routePaths.help.path} element={<HelpPage />} />
          {TempPage && (
            <Route
              path={routePaths.temp.path}
              element={
                <Suspense fallback={null}>
                  <TempPage />
                </Suspense>
              }
            />
          )}
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
