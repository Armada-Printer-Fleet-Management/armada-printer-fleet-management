import { SignInDialog } from '@armada/ui-kit';
import { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router';

import { SIGN_IN_REQUIRED_EVENT } from '../ipc/pywebview';
import { desktopSignInWording, useSignIn } from '../lib/use-sign-in';

// Asks the operator to sign in again over the current page when a call needs it.
export function SignInPrompt() {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState('');
  // "Not now" holds for the current page, which may keep polling; another page asks again.
  const dismissed = useRef(false);
  const { pathname } = useLocation();
  const close = () => setOpen(false);
  const dismiss = () => {
    dismissed.current = true;
    close();
  };
  const { state, start } = useSignIn(close);

  useEffect(() => {
    dismissed.current = false;
  }, [pathname]);

  useEffect(() => {
    const ask = (event: Event) => {
      // A polling page fails several calls a second; while the prompt is up or dismissed,
      // the rest are ignored.
      if (dismissed.current) return;
      setMessage(event instanceof CustomEvent ? String(event.detail) : '');
      setOpen(true);
    };
    window.addEventListener(SIGN_IN_REQUIRED_EVENT, ask);
    return () => window.removeEventListener(SIGN_IN_REQUIRED_EVENT, ask);
  }, []);

  return (
    <SignInDialog
      open={open}
      description={`${message} Your browser opens to finish signing in, and this page stays as it is.`}
      onDismiss={dismiss}
      status={state.status}
      error={state.error}
      onSignIn={start}
      onRestart={start}
      {...desktopSignInWording}
    />
  );
}
