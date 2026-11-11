import * as React from 'react';

import { cn } from '../lib/utils';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from './collapsible';
import {
  Dialog,
  DialogBody,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './dialog';

export interface LegalAgreementDocument {
  /** The document's display title, such as the licence's name. */
  title: string;
  /** The day this version took effect, YYYY-MM-DD. */
  effectiveDate: string;
  /** The document's text, or undefined when this build does not ship that version. */
  text: string | undefined;
}

export interface LegalAgreementDialogProps {
  /** The application the user is agreeing to use. */
  applicationTitle: string;
  /** Every document the user must accept, each in its own section, closed to start. */
  documents: LegalAgreementDocument[];
  onAcceptAll: () => void;
  /** True while the acceptances are being recorded. */
  accepting?: boolean;
  /** A plain-language reason the last attempt failed. */
  error?: string;
}

const button =
  'rounded-lg px-4 py-2 text-sm font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-60';

/**
 * Blocks the app until its legal documents are accepted, all at once. Each document opens on
 * demand, so the list stays short however many there are. Escape does not close it, and
 * declining explains why the app cannot continue, with the documents one click away.
 */
export function LegalAgreementDialog({
  applicationTitle,
  documents,
  onAcceptAll,
  accepting = false,
  error,
}: LegalAgreementDialogProps) {
  const [declined, setDeclined] = React.useState(false);
  const missing = documents.some((document) => document.text === undefined);

  return (
    <Dialog open>
      <DialogHeader>
        <DialogTitle>Before you use {applicationTitle}</DialogTitle>
        <DialogDescription>
          Review and accept the following to continue.
        </DialogDescription>
      </DialogHeader>

      <DialogBody className="overflow-y-auto">
        {declined ? (
          <p>
            {applicationTitle} can only be used once you accept these
            agreements. You can review them again whenever you are ready.
          </p>
        ) : (
          documents.map((document) => (
            <Collapsible key={`${document.title}-${document.effectiveDate}`}>
              <CollapsibleTrigger>
                <span className="flex-1">{document.title}</span>
                <span className="font-normal text-foreground/70">
                  Effective {document.effectiveDate}
                </span>
              </CollapsibleTrigger>
              <CollapsibleContent>
                {document.text === undefined ? (
                  <p role="alert">
                    This copy of {applicationTitle} does not include this
                    version of the document. Reload or update the app to read
                    it.
                  </p>
                ) : (
                  <pre
                    tabIndex={0}
                    aria-label={`${document.title} text`}
                    className="max-h-80 overflow-y-auto whitespace-pre-wrap rounded-lg border bg-background p-4 font-mono text-xs focus-visible:outline-2 focus-visible:outline-primary"
                  >
                    {document.text}
                  </pre>
                )}
              </CollapsibleContent>
            </Collapsible>
          ))
        )}
        {error && !declined && <p role="alert">{error}</p>}
      </DialogBody>

      <DialogFooter>
        {declined ? (
          <button
            type="button"
            className={cn(button, 'bg-primary text-primary-foreground')}
            onClick={() => setDeclined(false)}
          >
            Review again
          </button>
        ) : (
          <>
            <button
              type="button"
              className={cn(button, 'border bg-card')}
              disabled={accepting}
              onClick={() => setDeclined(true)}
            >
              Decline
            </button>
            <button
              type="button"
              className={cn(button, 'bg-primary px-6 text-primary-foreground')}
              disabled={accepting || missing}
              onClick={onAcceptAll}
            >
              {accepting ? 'Accepting…' : 'Accept All'}
            </button>
          </>
        )}
      </DialogFooter>
    </Dialog>
  );
}
