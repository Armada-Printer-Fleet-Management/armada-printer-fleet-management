// TEMPORARY: the desktop's entries on the shared vertical slice page. Delete this folder with
// packages/ui-kit/src/temp/. The 1 second polls here stand in for the real live updates.

import * as React from 'react';
import { type MessageInitShape, toJson } from '@bufbuild/protobuf';
import {
  TempVerticalSlicePage,
  type TempSliceOption,
  type TempSlicePoll,
  type TempSliceSection,
} from '@armada/ui-kit';
import type { File as StoredFile } from '../gen/file/v1/file_pb';
import {
  type PrintJob,
  PrintJobStatus,
  PrintJobStatusSchema,
} from '../gen/print_job/v1/print_job_pb';
import { type Printer, PrinterStatus } from '../gen/printer/v1/printer_pb';
import type { PrinterQueue } from '../gen/printer_queue/v1/printer_queue_pb';
import {
  ListPrintJobsResponseSchema,
  TransitionPrintJobRequestSchema,
  TransitionPrintJobResponseSchema,
} from '../gen/server/v1/print_job_service_pb';
import { ListPrinterQueuesResponseSchema } from '../gen/server/v1/printer_queue_service_pb';
import {
  ListPrintersResponseSchema,
  TransitionPrinterResponseSchema,
} from '../gen/server/v1/printer_service_pb';
import { listFiles } from '../ipc/file';
import { listPrintJobs, transitionPrintJob } from '../ipc/print-job';
import { listPrinters, transitionPrinter } from '../ipc/printer';
import { listPrinterQueues } from '../ipc/printer-queue';

type Action = MessageInitShape<
  typeof TransitionPrintJobRequestSchema
>['action'];

interface Snapshot {
  printJobs: PrintJob[];
  files: StoredFile[];
  printers: Printer[];
  printerQueues: PrinterQueue[];
}

const EMPTY: Snapshot = {
  printJobs: [],
  files: [],
  printers: [],
  printerQueues: [],
};

// The statuses staff can choose; the rest are set by the server or by dispatch.
const STATUS_ACTIONS: Partial<Record<number, (reason: string) => Action>> = {
  [PrintJobStatus.UNDER_REVIEW]: () => ({ case: 'startReview', value: {} }),
  [PrintJobStatus.APPROVED]: () => ({ case: 'approve', value: {} }),
  [PrintJobStatus.REJECTED]: (reason) => ({
    case: 'reject',
    value: { reason },
  }),
  [PrintJobStatus.COMPLETED]: () => ({ case: 'complete', value: {} }),
  [PrintJobStatus.FAILED]: (reason) => ({ case: 'fail', value: { reason } }),
};

const STATUS_OPTIONS: TempSliceOption[] = PrintJobStatusSchema.values
  .filter((v) => v.localName !== 'UNSPECIFIED')
  .map((v) => ({
    value: String(v.number),
    label: v.localName,
    disabled: STATUS_ACTIONS[v.number] === undefined,
  }));

async function transition(printJobId: string | undefined, action: Action) {
  if (!printJobId) throw new Error('Select a print job first.');
  return toJson(
    TransitionPrintJobResponseSchema,
    await transitionPrintJob({ printJobId: { value: printJobId }, action }),
  );
}

export function TempVerticalSlice() {
  const [snapshot, setSnapshot] = React.useState<Snapshot>(EMPTY);
  const [selected, setSelected] = React.useState<string>();

  // One poll per live status, as the final UI will have; each also feeds the workflow below.
  const printerPoll = React.useMemo<TempSlicePoll>(
    () => ({
      intervalMs: 1000,
      run: async () => {
        const response = await listPrinters();
        setSnapshot((s) => ({ ...s, printers: response.printers }));
        return toJson(ListPrintersResponseSchema, response);
      },
    }),
    [],
  );
  const queuePoll = React.useMemo<TempSlicePoll>(
    () => ({
      intervalMs: 1000,
      run: async () => {
        const response = await listPrinterQueues();
        setSnapshot((s) => ({ ...s, printerQueues: response.printerQueues }));
        return toJson(ListPrinterQueuesResponseSchema, response);
      },
    }),
    [],
  );
  const printJobPoll = React.useMemo<TempSlicePoll>(
    () => ({
      intervalMs: 1000,
      run: async () => {
        const response = await listPrintJobs({ page: { pageSize: 100 } });
        const fileIds = response.printJobs.flatMap((job) =>
          job.fileId ? [job.fileId] : [],
        );
        const { files } = await listFiles({ fileIds });
        setSnapshot((s) => ({ ...s, printJobs: response.printJobs, files }));
        return toJson(ListPrintJobsResponseSchema, response);
      },
    }),
    [],
  );

  const { printJobs, files, printers, printerQueues } = snapshot;
  const selectedJob = printJobs.find((job) => job.id?.value === selected);
  const filename = (job: PrintJob) =>
    files.find((file) => file.id?.value === job.fileId?.value)?.filename ??
    'no file';
  const queueName = (job: PrintJob) =>
    printerQueues.find((queue) => queue.id?.value === job.printerQueueId?.value)
      ?.name ?? 'no queue';
  const jobOption = (job: PrintJob): TempSliceOption => ({
    value: job.id?.value ?? '',
    label: filename(job),
  });
  const printerOption = (printer: Printer): TempSliceOption => ({
    value: printer.id?.value ?? '',
    label: printer.name,
  });

  function select(printJobId: string) {
    setSelected(printJobId);
    const job = printJobs.find(
      (candidate) => candidate.id?.value === printJobId,
    );
    // Opening a submitted job starts its review.
    if (job?.status === PrintJobStatus.SUBMITTED) {
      transition(printJobId, { case: 'startReview', value: {} }).catch(
        console.error,
      );
    }
  }

  const sections: TempSliceSection[] = [
    {
      title: 'Live status: printers',
      boundary: ['Desktop UI', 'IPC', 'Desktop backend', 'Connect', 'Server'],
      poll: printerPoll,
      actions: [],
    },
    {
      title: 'Live status: queues',
      boundary: ['Desktop UI', 'IPC', 'Desktop backend', 'Connect', 'Server'],
      poll: queuePoll,
      actions: [],
    },
    {
      title: 'Live status: print jobs',
      boundary: ['Desktop UI', 'IPC', 'Desktop backend', 'Connect', 'Server'],
      poll: printJobPoll,
      actions: [],
    },
    {
      title: 'Print jobs',
      boundary: ['Desktop UI', 'IPC', 'Desktop backend', 'Connect', 'Server'],
      list: {
        items: printJobs.map((job) => ({
          key: job.id?.value ?? '',
          label: [
            filename(job),
            `student ${job.userId?.value.slice(0, 8) ?? '?'}`,
            queueName(job),
            PrintJobStatus[job.status],
          ].join(' · '),
        })),
        selected,
        onSelect: select,
      },
      actions: [
        {
          label: 'Change status',
          resetKey: selected,
          fields: [
            {
              name: 'status',
              label: 'Status',
              options: STATUS_OPTIONS,
              defaultValue: selectedJob
                ? String(selectedJob.status)
                : undefined,
            },
            { name: 'reason', label: 'Reason (required to reject or fail)' },
          ],
          run: async ({ status = '', reason = '' }) => {
            const action = STATUS_ACTIONS[Number(status)];
            if (!action)
              throw new Error('Staff cannot set that status directly.');
            return transition(selected, action(reason));
          },
        },
        {
          label: 'Move to queue',
          resetKey: selected,
          fields: [
            {
              name: 'queue',
              label: 'Queue',
              options: printerQueues.map((queue) => ({
                value: queue.id?.value ?? '',
                label: queue.name,
                disabled: !queue.isActive,
              })),
            },
          ],
          run: async ({ queue = '' }) =>
            transition(selected, {
              case: 'moveToQueue',
              value: { printerQueueId: { value: queue } },
            }),
        },
      ],
    },
    {
      title: 'Dispatch',
      boundary: [
        'Desktop UI',
        'IPC',
        'Desktop backend',
        'Connect',
        'Server',
        'Printer server',
      ],
      actions: [
        {
          label: 'Dispatch',
          fields: [
            {
              name: 'job',
              label: 'Approved print job',
              options: printJobs
                .filter((job) => job.status === PrintJobStatus.APPROVED)
                .map(jobOption),
            },
            {
              name: 'printer',
              label: 'Idle printer',
              options: printers
                .filter((printer) => printer.status === PrinterStatus.IDLE)
                .map(printerOption),
            },
          ],
          run: async ({ job = '', printer = '' }) =>
            transition(job, {
              case: 'assign',
              value: { printerId: { value: printer } },
            }),
        },
        {
          label: 'Mark printer ready',
          fields: [
            {
              name: 'printer',
              label: 'Finished or faulted printer (cleared)',
              options: printers
                .filter(
                  (printer) =>
                    printer.status === PrinterStatus.FINISHED ||
                    printer.status === PrinterStatus.ERROR,
                )
                .map(printerOption),
            },
          ],
          run: async ({ printer = '' }) => {
            if (!printer) throw new Error('No printer is finished or faulted.');
            return toJson(
              TransitionPrinterResponseSchema,
              await transitionPrinter({
                printerId: { value: printer },
                action: { case: 'ready', value: {} },
              }),
            );
          },
        },
      ],
    },
  ];

  return (
    <TempVerticalSlicePage
      className="mt-8"
      heading="Vertical slice — desktop"
      sections={sections}
    />
  );
}
