// TEMPORARY: a dumping ground for vertical slice connections until the real UI exists. Delete this
// folder, its export in index.ts and each app's temp/ folder together.

import * as React from 'react';

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../components/card';
import { cn } from '../lib/utils';

export interface TempSliceAction {
  label: string;
  run: () => Promise<unknown>;
}

export interface TempSliceSection {
  title: string;
  /** The services a call crosses, in order, e.g. ['Desktop UI', 'IPC', 'Server']. */
  boundary: string[];
  actions: TempSliceAction[];
}

export interface TempVerticalSlicePageProps extends React.HTMLAttributes<HTMLElement> {
  heading: string;
  sections: TempSliceSection[];
}

type TempActionState =
  | { status: 'running' }
  | { status: 'done'; result: unknown }
  | { status: 'failed'; message: string };

const TempVerticalSlicePage = React.forwardRef<
  HTMLElement,
  TempVerticalSlicePageProps
>(({ heading, sections, className, ...props }, ref) => (
  <section ref={ref} className={cn('grid gap-6', className)} {...props}>
    <h2 className="text-2xl font-semibold">{heading}</h2>
    {sections.length === 0 && (
      <p className="text-sm text-foreground/70">No connections wired yet.</p>
    )}
    {sections.map((section) => (
      <TempSliceSectionCard key={section.title} section={section} />
    ))}
  </section>
));
TempVerticalSlicePage.displayName = 'TempVerticalSlicePage';

export { TempVerticalSlicePage };

function TempSliceSectionCard({ section }: { section: TempSliceSection }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{section.title}</CardTitle>
        <CardDescription className="text-foreground/70">
          <span className="sr-only">Boundary: </span>
          {section.boundary.join(' → ')}
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4">
        {section.actions.map((action) => (
          <TempSliceActionRow key={action.label} action={action} />
        ))}
      </CardContent>
    </Card>
  );
}

function TempSliceActionRow({ action }: { action: TempSliceAction }) {
  const [state, setState] = React.useState<TempActionState | undefined>();

  async function run() {
    setState({ status: 'running' });
    try {
      setState({ status: 'done', result: await action.run() });
    } catch (error: unknown) {
      setState({
        status: 'failed',
        message: error instanceof Error ? error.message : String(error),
      });
    }
  }

  return (
    <div className="grid gap-2">
      <button
        type="button"
        className="w-fit rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-50"
        disabled={state?.status === 'running'}
        onClick={() => void run()}
      >
        {action.label}
      </button>
      {state?.status === 'done' && (
        <pre className="overflow-x-auto rounded-lg border border-border p-3 text-xs">
          {JSON.stringify(state.result, null, 2)}
        </pre>
      )}
      {state?.status === 'failed' && (
        <p role="alert" className="text-sm">
          Failed: {state.message}
        </p>
      )}
    </div>
  );
}
