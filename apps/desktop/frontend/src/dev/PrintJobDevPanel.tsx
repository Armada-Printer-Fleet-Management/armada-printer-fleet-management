// TODO: TEMPORARY. A bare button proving the print job route works end to end. Replaced by the
// connection tester page (ARM-118, ARM-122, ARM-124); delete this file and its use in App.tsx then.

import { toJson } from '@bufbuild/protobuf';
import { useState } from 'react';
import { GetPrintJobResponseSchema } from '../gen/server/v1/print_job_service_pb';
import { printJob } from '../ipc/print-job';

// The submitted stub job seeded by the server's SqlPrintJobRepository.
const STUB_SUBMITTED_JOB_ID = '00000000-0000-4000-8000-000000000002';

export function PrintJobDevPanel() {
  const [result, setResult] = useState<string>('');

  async function getPrintJob() {
    try {
      const response = await printJob({
        printJobId: { value: STUB_SUBMITTED_JOB_ID },
      });
      setResult(
        JSON.stringify(toJson(GetPrintJobResponseSchema, response), null, 2),
      );
    } catch (error: unknown) {
      setResult(
        `Failed: ${error instanceof Error ? error.message : String(error)}`,
      );
    }
  }

  return (
    <section className="mt-6 flex items-start gap-4">
      <button
        type="button"
        className="rounded border px-3 py-1"
        onClick={() => void getPrintJob()}
      >
        GetPrintJob
      </button>
      <div className="text-sm">
        <p>
          Source: application server stub data, through the Python backend (IPC)
          and server.v1.PrintJobService/GetPrintJob.
        </p>
        {result && <pre className="mt-2 whitespace-pre-wrap">{result}</pre>}
      </div>
    </section>
  );
}
