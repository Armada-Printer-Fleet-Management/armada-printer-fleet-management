import { BrowserRouter, Navigate, Route, Routes } from 'react-router';

import App from './App';
import { StudentAppLayout } from './components/StudentAppLayout';
import { NotFoundPage } from './pages/NotFoundPage';
import { PrintJobStatusPage } from './pages/PrintJobStatusPage';
import { PrintSubmissionPage } from './pages/PrintSubmissionPage';
import { routePaths } from './routes';

export function WebRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<StudentAppLayout />}>
          <Route
            index
            element={<Navigate to={routePaths.integration.path} replace />}
          />
          <Route path={routePaths.integration.path} element={<App />} />
          <Route
            path={routePaths.printSubmission.path}
            element={<PrintSubmissionPage />}
          />
          <Route
            path={routePaths.printJobStatus.path}
            element={<PrintJobStatusPage />}
          />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
