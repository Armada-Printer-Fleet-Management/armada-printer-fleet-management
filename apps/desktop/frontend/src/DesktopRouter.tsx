import { HashRouter, Route, Routes } from 'react-router';

import { DesktopAppLayout } from './components/DesktopAppLayout';
import { devToolsEnabled } from './lib/dev-tools';
import { AboutPage } from './pages/AboutPage';
import { AccountPage } from './pages/AccountPage';
import { ActivityPage } from './pages/ActivityPage';
import { DashboardPage } from './pages/DashboardPage';
import { FleetPage } from './pages/FleetPage';
import { LoginPage } from './pages/LoginPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { QueuesPage } from './pages/QueuesPage';
import { SettingsPage } from './pages/SettingsPage';
import { StatisticsPage } from './pages/StatisticsPage';
import { TempPage } from './pages/TempPage';
import { UsersPage } from './pages/UsersPage';
import { routePaths } from './routes';

export function DesktopRoutes() {
  return (
    <Routes>
      <Route path={routePaths.login.path} element={<LoginPage />} />
      <Route element={<DesktopAppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path={routePaths.fleet.path} element={<FleetPage />} />
        <Route path={routePaths.queues.path} element={<QueuesPage />} />
        <Route path={routePaths.users.path} element={<UsersPage />} />
        <Route path={routePaths.statistics.path} element={<StatisticsPage />} />
        <Route path={routePaths.activity.path} element={<ActivityPage />} />
        <Route path={routePaths.settings.path} element={<SettingsPage />} />
        <Route path={routePaths.account.path} element={<AccountPage />} />
        <Route path={routePaths.about.path} element={<AboutPage />} />
        {devToolsEnabled() && (
          <Route path={routePaths.temp.path} element={<TempPage />} />
        )}
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

// Hash routing, because the default run mode loads index.html over file://.
export function DesktopRouter() {
  return (
    <HashRouter>
      <DesktopRoutes />
    </HashRouter>
  );
}
