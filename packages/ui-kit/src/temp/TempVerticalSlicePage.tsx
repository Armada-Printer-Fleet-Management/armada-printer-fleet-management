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

export interface TempSliceOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface TempSliceField {
  name: string;
  label: string;
  /** A select of these options; without them the field is a text input. */
  options?: TempSliceOption[];
  defaultValue?: string;
}

export interface TempSliceAction {
  label: string;
  fields?: TempSliceField[];
  /** Changing it clears what was typed or chosen, e.g. when a different item is selected. */
  resetKey?: string;
  run: (values: Record<string, string>) => Promise<unknown>;
}

export interface TempSliceListItem {
  key: string;
  label: string;
}

export interface TempSliceList {
  items: TempSliceListItem[];
  selected?: string;
  onSelect: (key: string) => void;
}

export interface TempSlicePoll {
  intervalMs: number;
  run: () => Promise<unknown>;
}

export interface TempSliceSection {
  title: string;
  /** The services a call crosses, in order, e.g. ['Desktop UI', 'IPC', 'Server']. */
  boundary: string[];
  actions: TempSliceAction[];
  /** Runs on an interval and shows its latest result. */
  poll?: TempSlicePoll;
  list?: TempSliceList;
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
        {section.poll && <TempSlicePollView poll={section.poll} />}
        {section.list && <TempSliceListView list={section.list} />}
        {section.actions.map((action) => (
          <TempSliceActionRow
            key={`${action.label}:${action.resetKey ?? ''}`}
            action={action}
          />
        ))}
      </CardContent>
    </Card>
  );
}

const inputClass =
  'rounded-lg border border-border bg-background px-2 py-1 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary';

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : String(error);
}

function TempSliceResult({ state }: { state: TempActionState | undefined }) {
  return (
    <>
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
    </>
  );
}

function TempSlicePollView({ poll }: { poll: TempSlicePoll }) {
  const [state, setState] = React.useState<TempActionState | undefined>();

  React.useEffect(() => {
    let cancelled = false;
    async function tick() {
      try {
        const result = await poll.run();
        if (!cancelled) setState({ status: 'done', result });
      } catch (error: unknown) {
        if (!cancelled)
          setState({ status: 'failed', message: errorMessage(error) });
      }
    }
    void tick();
    const timer = setInterval(() => void tick(), poll.intervalMs);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [poll]);

  return <TempSliceResult state={state} />;
}

function TempSliceListView({ list }: { list: TempSliceList }) {
  if (list.items.length === 0) {
    return <p className="text-sm text-foreground/70">Nothing to show.</p>;
  }
  return (
    <ul className="grid gap-1">
      {list.items.map((item) => (
        <li key={item.key}>
          <button
            type="button"
            aria-pressed={item.key === list.selected}
            className={cn(
              'w-full rounded-lg border border-border px-3 py-1.5 text-left text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary',
              item.key === list.selected &&
                'bg-primary text-primary-foreground',
            )}
            onClick={() => list.onSelect(item.key)}
          >
            {item.label}
          </button>
        </li>
      ))}
    </ul>
  );
}

function TempSliceActionRow({ action }: { action: TempSliceAction }) {
  const [state, setState] = React.useState<TempActionState | undefined>();
  const [chosen, setChosen] = React.useState<Record<string, string>>({});
  const id = React.useId();

  function valueOf(field: TempSliceField) {
    return (
      chosen[field.name] ??
      field.defaultValue ??
      field.options?.find((option) => !option.disabled)?.value ??
      ''
    );
  }

  async function run() {
    const values = Object.fromEntries(
      (action.fields ?? []).map((field) => [field.name, valueOf(field)]),
    );
    setState({ status: 'running' });
    try {
      setState({ status: 'done', result: await action.run(values) });
    } catch (error: unknown) {
      setState({ status: 'failed', message: errorMessage(error) });
    }
  }

  return (
    <div className="grid gap-2">
      {action.fields?.map((field) => {
        const fieldId = `${id}-${field.name}`;
        const onChange = (
          event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
        ) => setChosen({ ...chosen, [field.name]: event.target.value });
        return (
          <label
            key={field.name}
            htmlFor={fieldId}
            className="grid gap-1 text-sm"
          >
            {field.label}
            {field.options ? (
              <select
                id={fieldId}
                className={inputClass}
                value={valueOf(field)}
                onChange={onChange}
              >
                {field.options.map((option) => (
                  <option
                    key={option.value}
                    value={option.value}
                    disabled={option.disabled}
                  >
                    {option.label}
                  </option>
                ))}
              </select>
            ) : (
              <input
                id={fieldId}
                className={inputClass}
                value={valueOf(field)}
                onChange={onChange}
              />
            )}
          </label>
        );
      })}
      <button
        type="button"
        className="w-fit rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-50"
        disabled={state?.status === 'running'}
        onClick={() => void run()}
      >
        {action.label}
      </button>
      <TempSliceResult state={state} />
    </div>
  );
}
