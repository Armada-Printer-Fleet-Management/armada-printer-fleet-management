import type { SignInStatus } from '@armada/ui-kit';
import { useRef, useState } from 'react';

import { signIn } from '../ipc/session';

export interface SignInState {
  status: SignInStatus;
  error?: string;
}

// The desktop's wording for its browser round trip, shown by the shared sign-in controls.
export const desktopSignInWording = {
  waitingLabel: 'Waiting for your browser…',
  waitingHint: 'Finish signing in in your browser, then return here.',
  restartLabel: 'Closed the tab? Open the sign-in page again',
};

// Runs the browser sign-in. Calling start() again restarts it, and the earlier attempt's result
// is ignored, so only the latest one may change the screen.
export function useSignIn(onSignedIn: () => void) {
  const [state, setState] = useState<SignInState>({ status: 'idle' });
  const attempt = useRef(0);

  const start = () => {
    const current = ++attempt.current;
    setState({ status: 'waiting' });
    signIn()
      .then(() => {
        if (current !== attempt.current) return;
        setState({ status: 'idle' });
        onSignedIn();
      })
      .catch((error: unknown) => {
        if (current !== attempt.current) return;
        setState({
          status: 'error',
          error: error instanceof Error ? error.message : String(error),
        });
      });
  };

  return { state, start };
}
