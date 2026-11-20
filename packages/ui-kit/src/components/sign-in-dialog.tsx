import * as React from 'react';

import { cn } from '../lib/utils';
import { Dialog, DialogDescription, DialogHeader, DialogTitle } from './dialog';
import { SignInControls, type SignInControlsProps } from './sign-in-controls';

export interface SignInDialogProps extends Omit<
  SignInControlsProps,
  'title' | 'className'
> {
  open: boolean;
  title?: string;
  /** Why the user is being asked, and what signing in involves. */
  description: React.ReactNode;
  /** Called on Escape or the dismiss button. */
  onDismiss: () => void;
  dismissLabel?: string;
  className?: string;
}

/** Asks the user to sign in over the current page, so they keep their place. */
const SignInDialog = React.forwardRef<HTMLDialogElement, SignInDialogProps>(
  (
    {
      open,
      title = 'Sign in to continue',
      description,
      onDismiss,
      dismissLabel = 'Not now',
      className,
      ...controls
    },
    ref,
  ) => (
    <Dialog
      ref={ref}
      open={open}
      onDismiss={onDismiss}
      className={cn('w-[min(24rem,calc(100vw-2rem))]', className)}
    >
      <DialogHeader>
        <DialogTitle>{title}</DialogTitle>
        <DialogDescription>{description}</DialogDescription>
      </DialogHeader>
      <SignInControls {...controls} />
      <button
        type="button"
        onClick={onDismiss}
        className="justify-self-center self-center rounded-md text-sm text-foreground/70 underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
      >
        {dismissLabel}
      </button>
    </Dialog>
  ),
);
SignInDialog.displayName = 'SignInDialog';

export { SignInDialog };
