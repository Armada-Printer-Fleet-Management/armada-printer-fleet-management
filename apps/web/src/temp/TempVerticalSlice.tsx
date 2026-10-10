// TEMPORARY: the web app's entries on the shared vertical slice page. Delete this folder with
// packages/ui-kit/src/temp/.

import {
  type JsonValue,
  type MessageInitShape,
  create,
  fromJson,
  toJson,
} from '@bufbuild/protobuf';
import { TempVerticalSlicePage, type TempSliceSection } from '@armada/ui-kit';
import {
  GetPrintJobRequestSchema,
  GetPrintJobResponseSchema,
  PrintJobService,
} from '../gen/server/v1/print_job_service_pb';

// The submitted stub job seeded by the server's in-memory print job store.
const TEMP_STUB_SUBMITTED_JOB_ID = '00000000-0000-4000-8000-000000000002';

// TODO - Replace this API example call with a proper API architecture.
async function tempPrintJob(
  request: MessageInitShape<typeof GetPrintJobRequestSchema>,
) {
  const response = await fetch(
    `/api/${PrintJobService.typeName}/${PrintJobService.method.getPrintJob.name}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(
        toJson(
          GetPrintJobRequestSchema,
          create(GetPrintJobRequestSchema, request),
        ),
      ),
    },
  );
  // A parsed JSON body is a JsonValue by definition; fetch only types it as any.
  const body = (await response.json()) as JsonValue;
  if (!response.ok) {
    const message =
      typeof body === 'object' && body !== null && !Array.isArray(body)
        ? body['message']
        : undefined;
    throw new Error(
      typeof message === 'string' ? message : `HTTP ${response.status}`,
    );
  }
  return fromJson(GetPrintJobResponseSchema, body);
}

const TEMP_SECTIONS: TempSliceSection[] = [
  {
    title: 'Print jobs',
    boundary: ['Web UI', 'HTTP (Connect JSON)', 'Server'],
    actions: [
      {
        label: 'GetPrintJob',
        run: async () =>
          toJson(
            GetPrintJobResponseSchema,
            await tempPrintJob({
              printJobId: { value: TEMP_STUB_SUBMITTED_JOB_ID },
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
      heading="Vertical slice — web"
      sections={TEMP_SECTIONS}
    />
  );
}
