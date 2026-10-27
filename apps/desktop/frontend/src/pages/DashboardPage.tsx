import { routePaths } from '../routes';

export function DashboardPage() {
  return <h1 className="text-3xl font-bold">{routePaths.dashboard.label}</h1>;
}
