import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  SignInControls,
} from '@armada/ui-kit';
import { Link, useNavigate } from 'react-router';

import { desktopSignInWording, useSignIn } from '../lib/use-sign-in';
import { routePaths } from '../routes';

export function LoginPage() {
  const navigate = useNavigate();
  const { state, start } = useSignIn(
    () => void navigate(routePaths.dashboard.path),
  );

  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-4 text-foreground">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>{routePaths.login.label}</CardTitle>
          <p className="text-sm text-muted-foreground">
            Sign in with your organization account. Your browser opens to finish
            signing in.
          </p>
        </CardHeader>
        <CardContent className="grid gap-4">
          <SignInControls
            status={state.status}
            error={state.error}
            onSignIn={start}
            onRestart={start}
            {...desktopSignInWording}
          />

          <Link
            to={routePaths.dashboard.path}
            className="justify-self-center rounded-md text-sm text-muted-foreground underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
          >
            Continue without signing in
          </Link>
        </CardContent>
      </Card>
    </main>
  );
}
