import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@armada/ui-kit';
import { useState } from 'react';

import { exportLogs, writeTestLog } from '../ipc/logs';
import { routePaths } from '../routes';

type DiagnosticsState =
  | { status: 'idle' }
  | { status: 'busy'; action: 'test' | 'export' }
  | { status: 'done'; message: string }
  | { status: 'error'; message: string };

const buttonBase =
  'w-fit rounded-md px-4 py-2 font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-60';

export function SettingsPage() {
  return (
    <section className="grid gap-6">
      <h1 className="text-3xl font-bold">{routePaths.settings.label}</h1>
      <DiagnosticsCard />
    </section>
  );
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : String(error);
}

function DiagnosticsCard() {
  const [state, setState] = useState<DiagnosticsState>({ status: 'idle' });
  const busy = state.status === 'busy';

  async function handleTestLog() {
    setState({ status: 'busy', action: 'test' });
    try {
      await writeTestLog();
      setState({
        status: 'done',
        message: 'Test entry written to the log file.',
      });
    } catch (error: unknown) {
      setState({
        status: 'error',
        message: `Could not write the test entry: ${errorMessage(error)}.`,
      });
    }
  }

  async function handleExport() {
    setState({ status: 'busy', action: 'export' });
    try {
      const result = await exportLogs();
      setState(
        result.cancelled
          ? { status: 'idle' }
          : { status: 'done', message: `Logs saved to ${result.path}` },
      );
    } catch (error: unknown) {
      setState({
        status: 'error',
        message: `Could not export the logs: ${errorMessage(error)}. Try again, or choose a different folder.`,
      });
    }
  }

  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <CardTitle className="text-xl">Diagnostics</CardTitle>
        <CardDescription>
          Save the application&apos;s logs as a zip file to send to the
          developers when reporting a problem. Write a test entry to check that
          logging works.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3">
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => void handleExport()}
            disabled={busy}
            className={`${buttonBase} bg-primary text-primary-foreground hover:bg-primary/90`}
          >
            {state.status === 'busy' && state.action === 'export'
              ? 'Exporting…'
              : 'Export logs'}
          </button>
          <button
            type="button"
            onClick={() => void handleTestLog()}
            disabled={busy}
            className={`${buttonBase} border border-border bg-background text-foreground hover:bg-foreground/5`}
          >
            Write test log entry
          </button>
        </div>
        <p role="status" className="text-sm">
          {(state.status === 'done' || state.status === 'error') &&
            state.message}
        </p>
      </CardContent>
    </Card>
  );
}
