import { Link } from 'react-router';

import { routePaths } from '../routes';

export function NotFoundPage() {
  return (
    <main className="min-h-full bg-background p-8 text-foreground">
      <div className="mx-auto max-w-2xl">
        <section className="grid gap-3">
          <h1 className="text-3xl font-bold">Page not found</h1>
          <p className="text-sm text-foreground/70">
            The page you requested does not exist.
          </p>
          <Link
            to={routePaths.integration.path}
            className="w-fit rounded-md text-sm font-medium text-primary underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
          >
            Return to integration testing
          </Link>
        </section>
      </div>
    </main>
  );
}
