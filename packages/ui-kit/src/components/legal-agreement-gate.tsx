import * as React from 'react';

import {
  Dialog,
  DialogBody,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './dialog';
import { LegalAgreementDialog } from './legal-agreement-dialog';

/** The fields of a legal document the gate shows. The generated LegalDocument message fits. */
export interface LegalDocumentView {
  title: string;
  effectiveDate: string;
  sha256: string;
}

export interface LegalAgreementGateProps<Document extends LegalDocumentView> {
  applicationTitle: string;
  /** Each document's text this build ships, keyed by its SHA-256. */
  texts: Readonly<Record<string, string>>;
  /** The documents the user has not accepted yet. */
  loadOutstanding: () => Promise<Document[]>;
  /** Records that the user accepted one of them. */
  accept: (document: Document) => Promise<void>;
  children: React.ReactNode;
}

type State<Document> =
  | { kind: 'checking' }
  | { kind: 'unreachable' }
  | { kind: 'ready'; outstanding: Document[] };

/**
 * Renders the app only once every current legal document is accepted, showing each outstanding
 * one in turn. If they cannot be checked, the app stays blocked and offers a retry.
 */
export function LegalAgreementGate<Document extends LegalDocumentView>({
  applicationTitle,
  texts,
  loadOutstanding,
  accept,
  children,
}: LegalAgreementGateProps<Document>) {
  const [state, setState] = React.useState<State<Document>>({
    kind: 'checking',
  });
  const [accepting, setAccepting] = React.useState(false);
  const [error, setError] = React.useState<string>();

  const load = React.useCallback(
    () =>
      loadOutstanding().then(
        (outstanding) => setState({ kind: 'ready', outstanding }),
        () => setState({ kind: 'unreachable' }),
      ),
    [loadOutstanding],
  );

  React.useEffect(() => {
    void load();
  }, [load]);

  const retry = () => {
    setState({ kind: 'checking' });
    void load();
  };

  if (state.kind === 'checking') {
    return (
      <p role="status" className="p-6 text-sm text-foreground/70">
        Checking the agreements for {applicationTitle}…
      </p>
    );
  }

  if (state.kind === 'unreachable') {
    return (
      <Dialog open>
        <DialogHeader>
          <DialogTitle>Could not check the agreements</DialogTitle>
          <DialogDescription>
            {applicationTitle} needs to confirm you have accepted its licence
            before it opens.
          </DialogDescription>
        </DialogHeader>
        <DialogBody>
          <p>
            The server could not be reached. Check your connection, then retry.
          </p>
        </DialogBody>
        <DialogFooter>
          <button
            type="button"
            className="rounded-lg bg-primary px-6 py-2 text-sm font-medium text-primary-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
            onClick={retry}
          >
            Retry
          </button>
        </DialogFooter>
      </Dialog>
    );
  }

  const { outstanding } = state;
  if (outstanding.length === 0) return <>{children}</>;

  const onAcceptAll = () => {
    setAccepting(true);
    setError(undefined);
    // Each one that is saved leaves the list, so a retry after a failure sends only the rest.
    void Promise.allSettled(
      outstanding.map((document) => accept(document)),
    ).then((results) => {
      setAccepting(false);
      const left = outstanding.filter(
        (_, i) => results[i]?.status !== 'fulfilled',
      );
      setState({ kind: 'ready', outstanding: left });
      if (left.length > 0) {
        setError(
          'Your acceptance could not be saved. Check your connection, then accept again.',
        );
      }
    });
  };

  return (
    <LegalAgreementDialog
      applicationTitle={applicationTitle}
      documents={outstanding.map((document) => ({
        title: document.title,
        effectiveDate: document.effectiveDate,
        text: texts[document.sha256],
      }))}
      onAcceptAll={onAcceptAll}
      accepting={accepting}
      error={error}
    />
  );
}
