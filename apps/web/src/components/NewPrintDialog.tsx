import { cn, Dialog } from '@armada/ui-kit';
import { useRef, useState, type FormEvent } from 'react';

import { apiClient } from '../lib/api';
import {
  PrintSubmission,
  validateFile,
  type SubmissionState,
} from '../lib/print-submission';

const api = apiClient.printJobs;

const progress: Partial<Record<SubmissionState['phase'], string>> = {
  hashing: 'Checking the file...',
  creating: 'Creating your draft...',
  slot: 'Preparing the upload...',
  uploading: 'Uploading your file...',
  submitting: 'Submitting your print...',
  checking: 'Checking the submission status...',
};

export function SubmissionFeedback({
  state,
  onClose,
}: {
  state: SubmissionState;
  onClose: () => void;
}) {
  const message = progress[state.phase];
  if (message) return <p role="status">{message}</p>;
  if (state.phase === 'success')
    return (
      <div className="grid gap-3">
        <p role="status">Your print has been submitted.</p>
        <button
          type="button"
          onClick={onClose}
          className="min-h-10 rounded-lg bg-primary px-4 font-semibold text-primary-foreground cursor-pointer hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
        >
          Done
        </button>
      </div>
    );
  if (!('message' in state)) return null;

  return (
    <div role="alert" className="rounded-lg border border-border bg-card p-4">
      <p>{state.message}</p>
      {state.phase === 'unknown-create' && (
        <p>
          The draft may have been created. Check with staff before starting
          another submission.
        </p>
      )}
      {state.phase === 'unknown' && (
        <p>
          The submission status is unknown. Check the status again before
          submitting another job.
        </p>
      )}
    </div>
  );
}

export function FileDetails({ file }: { file: File | null }) {
  const formatSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    const index = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, index)).toFixed(1)} ${units[index]}`;
  };

  return (
    <p id="file-details" className="text-sm">
      {file ? `${file.name} — ${formatSize(file.size)}` : 'No file selected.'}
    </p>
  );
}

export function NewPrintDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [notes, setNotes] = useState('');
  const [validationError, setValidationError] = useState<string>();
  const [state, setState] = useState<SubmissionState>({ phase: 'ready' });
  const submission = useRef<PrintSubmission | null>(null);
  const active = useRef(false);
  const fileInput = useRef<HTMLInputElement | null>(null);
  const editable =
    state.phase === 'ready' || state.phase === 'failed-preparation';
  const busy = progress[state.phase] !== undefined;

  function close() {
    if (active.current) return;
    if (
      state.phase !== 'success' &&
      (file !== null || notes.length > 0) &&
      !window.confirm(
        'Discard this form? Any draft already created on the server will remain and cannot be retried from this form.',
      )
    ) {
      return;
    }
    setFile(null);
    setNotes('');
    setValidationError(undefined);
    setState({ phase: 'ready' });
    submission.current = null;
    if (fileInput.current) fileInput.current.value = '';
    onClose();
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editable || active.current) return;
    const error =
      validateFile(file) ??
      (notes.length > 1000
        ? 'Notes must be 1000 characters or fewer.'
        : undefined);
    if (error || !file) {
      setValidationError(error);
      return;
    }
    setValidationError(undefined);
    const next = new PrintSubmission(api, file, notes, setState);
    submission.current = next;
    active.current = true;
    void next.start().finally(() => {
      active.current = false;
    });
  }

  function retry() {
    if (active.current || !submission.current) return;
    active.current = true;
    void submission.current.retry().finally(() => {
      active.current = false;
    });
  }

  return (
    <Dialog
      open={open}
      onDismiss={close}
      onCancel={(event) => {
        const target = event.target as HTMLElement;
        if (
          target.tagName === 'INPUT' &&
          (target as HTMLInputElement).type === 'file'
        ) {
          event.preventDefault();
        }
      }}
      aria-labelledby="new-print-title"
    >
      <div className="max-w-2xl p-8">
        <div className="flex items-start justify-between gap-4">
          <h2 id="new-print-title" className="text-3xl font-bold">
            New print
          </h2>
          <button
            type="button"
            onClick={close}
            disabled={busy}
            aria-label="Close new print"
            className="min-h-10 min-w-10 cursor-pointer rounded-lg border border-border enabled:hover:border-primary enabled:hover:text-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:cursor-not-allowed disabled:opacity-50"
          >
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
        <form className="mt-6 grid gap-6" onSubmit={submit} noValidate>
          <div className="grid gap-2">
            <p id="print-file-label" className="font-semibold">
              Print file
            </p>
            <p id="file-help" className="text-sm">
              Choose one .gcode file. Maximum 500 MB.
            </p>
            <div
              className={cn(
                'group/file rounded-lg border border-border bg-card',
                editable && 'hover:border-primary',
              )}
            >
              <input
                id="print-file"
                ref={fileInput}
                type="file"
                accept=".gcode,.cgcode"
                aria-labelledby="print-file-label"
                aria-describedby="file-help file-details"
                disabled={!editable}
                onChange={(event) => {
                  setFile(event.currentTarget.files?.[0] ?? null);
                  setValidationError(undefined);
                }}
                className={cn(
                  'block w-full cursor-pointer rounded-lg p-3 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:cursor-not-allowed disabled:opacity-50',
                  'file:mr-3 file:cursor-pointer file:rounded-md file:border file:border-border file:bg-background file:px-3 file:py-1 file:font-medium file:text-foreground disabled:file:cursor-not-allowed',
                  editable && 'group-hover/file:file:bg-foreground/10',
                  file ? 'text-foreground' : 'text-foreground/70',
                )}
              />
            </div>
            <FileDetails file={file} />
          </div>
          <div className="grid gap-2">
            <label htmlFor="print-notes" className="font-semibold">
              Notes for staff (optional)
            </label>
            <textarea
              id="print-notes"
              maxLength={1000}
              value={notes}
              disabled={!editable}
              onChange={(event) => setNotes(event.currentTarget.value)}
              aria-describedby="notes-help"
              rows={6}
              className="w-full min-h-24 rounded-lg border border-border bg-card p-3 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
            />
            <p id="notes-help" className="text-sm">
              {notes.length} / 1000 characters
            </p>
          </div>
          {validationError && <p role="alert">{validationError}</p>}
          <SubmissionFeedback state={state} onClose={close} />
          {editable && (
            <button
              type="submit"
              className="min-h-10 rounded-lg bg-primary px-4 font-semibold text-primary-foreground enabled:cursor-pointer enabled:hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
            >
              Submit print
            </button>
          )}
          {(state.phase === 'failed-upload' ||
            state.phase === 'failed-submit' ||
            state.phase === 'unknown') && (
            <button
              type="button"
              onClick={retry}
              className="min-h-10 rounded-lg bg-primary px-4 font-semibold text-primary-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
            >
              {state.phase === 'unknown' ? 'Check status again' : 'Retry'}
            </button>
          )}
        </form>
      </div>
    </Dialog>
  );
}
