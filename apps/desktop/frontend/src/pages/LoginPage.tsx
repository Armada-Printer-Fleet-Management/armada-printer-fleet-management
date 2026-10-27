import { Link } from 'react-router';

import { routePaths } from '../routes';

export function LoginPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background text-foreground">
      <h1 className="text-3xl font-bold">{routePaths.login.label}</h1>
      <Link
        to={routePaths.dashboard.path}
        className="rounded-md text-sm font-medium text-primary underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
      >
        Continue to {routePaths.dashboard.label}
      </Link>
    </main>
  );
}
