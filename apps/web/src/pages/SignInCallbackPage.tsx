import type { User } from 'oidc-client-ts';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router';

import { userManager } from '../lib/auth';
import { routePaths } from '../routes';

// Shared across effect runs: StrictMode runs the effect twice, and the one-time sign-in code in the
// URL can only be redeemed once.
let pending: Promise<User> | undefined;

function completeSignIn(): Promise<User> {
  pending ??= userManager.signinRedirectCallback();
  return pending;
}

// Only an in-app path is followed. Browsers read "//host" and "/\host" as another site.
function returnPath(state: unknown): string {
  const inApp =
    typeof state === 'string' &&
    state.startsWith('/') &&
    !state.startsWith('//') &&
    !state.startsWith('/\\');
  return inApp ? state : routePaths.home.path;
}

export function SignInCallbackPage() {
  const navigate = useNavigate();
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    completeSignIn()
      .then((user) => {
        if (!cancelled) {
          void navigate(returnPath(user.state), { replace: true });
        }
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [navigate]);

  if (!failed) {
    return (
      <p role="status" className="p-8 text-foreground/70">
        Signing you in…
      </p>
    );
  }

  return (
    <section className="grid gap-3 p-8">
      <h1 className="text-3xl font-bold">We couldn’t sign you in</h1>
      <p className="text-foreground/80">
        The sign-in didn’t complete. Go back and try again.
      </p>
      <Link
        to={routePaths.home.path}
        className="w-fit rounded-md text-sm font-medium text-primary underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
      >
        Return to {routePaths.home.label}
      </Link>
    </section>
  );
}
