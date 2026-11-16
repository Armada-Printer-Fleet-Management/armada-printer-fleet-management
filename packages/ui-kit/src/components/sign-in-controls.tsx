import * as React from 'react';

import { cn } from '../lib/utils';

export type SignInStatus = 'idle' | 'waiting' | 'error';

export interface SignInControlsProps extends React.HTMLAttributes<HTMLDivElement> {
  status: SignInStatus;
  /** A plain-language reason the last attempt failed, shown when status is 'error'. */
  error?: string;
  onSignIn: () => void;
  /** The button's text while signing in. */
  waitingLabel?: string;
  /** What the user should do while signing in, such as finishing in another window. */
  waitingHint?: React.ReactNode;
  /** Starts sign-in again while waiting. The restart link is shown only when this is given. */
  onRestart?: () => void;
  restartLabel?: string;
}

const focusRing =
  'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary';

/** The Sign in button and what it reports while signing in or after a failure. */
const SignInControls = React.forwardRef<HTMLDivElement, SignInControlsProps>(
  (
    {
      status,
      error,
      onSignIn,
      waitingLabel = 'Signing in…',
      waitingHint,
      onRestart,
      restartLabel = 'Start signing in again',
      className,
      ...props
    },
    ref,
  ) => {
    const waiting = status === 'waiting';
    return (
      <div ref={ref} className={cn('grid gap-4', className)} {...props}>
        <button
          type="button"
          onClick={onSignIn}
          disabled={waiting}
          className={cn(
            'h-11 w-full rounded-md bg-primary text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:cursor-wait disabled:opacity-70',
            focusRing,
          )}
        >
          {waiting ? waitingLabel : 'Sign in'}
        </button>

        <div aria-live="polite" className="grid gap-2 text-sm">
          {waiting && waitingHint !== undefined && <p>{waitingHint}</p>}
          {waiting && onRestart && (
            <button
              type="button"
              onClick={onRestart}
              className={cn(
                'justify-self-start rounded-md font-medium text-primary underline-offset-4 hover:underline',
                focusRing,
              )}
            >
              {restartLabel}
            </button>
          )}
          {status === 'error' && error && <p role="alert">{error}</p>}
        </div>
      </div>
    );
  },
);
SignInControls.displayName = 'SignInControls';

export { SignInControls };
