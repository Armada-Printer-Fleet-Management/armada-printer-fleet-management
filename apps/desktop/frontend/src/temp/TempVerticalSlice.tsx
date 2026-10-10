// TEMPORARY: the desktop's entries on the shared vertical slice page. Delete this folder with
// packages/ui-kit/src/temp/.

import { toJson } from '@bufbuild/protobuf';
import { TempVerticalSlicePage, type TempSliceSection } from '@armada/ui-kit';
import {
  GetPrintJobResponseSchema,
  TransitionPrintJobResponseSchema,
} from '../gen/server/v1/print_job_service_pb';
import { printJob, transitionPrintJob } from '../ipc/print-job';

// The submitted stub job seeded by the server's in-memory print job store.
const TEMP_STUB_SUBMITTED_JOB_ID = '00000000-0000-4000-8000-000000000002';

const TEMP_SECTIONS: TempSliceSection[] = [
  {
    title: 'Print jobs',
    boundary: ['Desktop UI', 'IPC', 'Desktop backend', 'Connect', 'Server'],
    actions: [
      {
        label: 'GetPrintJob',
        run: async () =>
          toJson(
            GetPrintJobResponseSchema,
            await printJob({
              printJobId: { value: TEMP_STUB_SUBMITTED_JOB_ID },
            }),
          ),
      },
      {
        label: 'StartReview',
        run: async () =>
          toJson(
            TransitionPrintJobResponseSchema,
            await transitionPrintJob({
              printJobId: { value: TEMP_STUB_SUBMITTED_JOB_ID },
              action: { case: 'startReview', value: {} },
            }),
          ),
      },
    ],
  },
];

export function TempVerticalSlice() {
  return (
    <TempVerticalSlicePage
      className="mt-8"
      heading="Vertical slice — desktop"
      sections={TEMP_SECTIONS}
    />
  );
}
