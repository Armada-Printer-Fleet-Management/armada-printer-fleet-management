// TEMPORARY: the web app's entries on the shared vertical slice page. Delete this folder with
// packages/ui-kit/src/temp/.

import { toJson } from '@bufbuild/protobuf';
import { TempVerticalSlicePage, type TempSliceSection } from '@armada/ui-kit';
import type { createApiClient } from '@armada/api-client';
import {
  GetPrintJobResponseSchema,
  ListPrintJobsResponseSchema,
} from '@armada/api-client/gen/server/v1/print_job_service_pb';

type PrintJobsApi = ReturnType<typeof createApiClient>['printJobs'];

export function TempVerticalSlice({ printJobs }: { printJobs: PrintJobsApi }) {
  const sections: TempSliceSection[] = [
    {
      title: 'Print jobs',
      boundary: ['Web UI', 'ConnectRPC', 'Server'],
      actions: [
        {
          label: 'ListPrintJobs',
          run: async () =>
            toJson(
              ListPrintJobsResponseSchema,
              await printJobs.listPrintJobs({ page: { pageSize: 20 } }),
            ),
        },
        {
          label: 'GetPrintJob',
          run: async () => {
            const page = await printJobs.listPrintJobs({
              page: { pageSize: 1 },
            });
            const firstJob = page.printJobs[0];
            if (!firstJob) {
              throw new Error('No print jobs are available to retrieve.');
            }
            return toJson(
              GetPrintJobResponseSchema,
              await printJobs.getPrintJob({ printJobId: firstJob.id }),
            );
          },
        },
      ],
    },
  ];

  return (
    <TempVerticalSlicePage
      className="mt-8"
      heading="Vertical slice — web"
      sections={sections}
    />
  );
}
