import { Link } from 'react-router';

import { routePaths } from '../routes';

export function NotFoundPage() {
  return (
    <section className="grid gap-3">
      <h1 className="text-3xl font-bold">Page not found</h1>
      <Link
        to={routePaths.dashboard.path}
        className="w-fit rounded-md text-sm font-medium text-primary underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
      >
        Return to {routePaths.dashboard.label}
      </Link>
    </section>
  );
}
