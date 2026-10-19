import type { MessageInitShape } from '@bufbuild/protobuf';
import type { Client } from '@connectrpc/connect';
import type { FileUploadSlot } from './gen/file/v1/file_upload_pb';
import {
  CreatePrintJobRequestSchema,
  CreatePrintJobUploadRequestSchema,
  GetPrintJobRequestSchema,
  ListPrintJobsRequestSchema,
  PrintJobService,
  SubmitPrintJobRequestSchema,
} from './gen/server/v1/print_job_service_pb';
import { PrintJobUploadError } from './errors';

type PrintJobRpcClient = Pick<
  Client<typeof PrintJobService>,
  | 'createPrintJob'
  | 'createPrintJobUpload'
  | 'submitPrintJob'
  | 'listPrintJobs'
  | 'getPrintJob'
>;

export function createPrintJobApi(
  client: PrintJobRpcClient,
  uploadFetch: typeof globalThis.fetch = globalThis.fetch,
) {
  return {
    createPrintJob: (
      request: MessageInitShape<typeof CreatePrintJobRequestSchema>,
    ) => client.createPrintJob(request),
    createPrintJobUpload: (
      request: MessageInitShape<typeof CreatePrintJobUploadRequestSchema>,
    ) => client.createPrintJobUpload(request),
    uploadPrintJobFile: async (slot: FileUploadSlot, file: Blob) => {
      const response = await uploadFetch(slot.uploadUrl, {
        method: 'PUT',
        body: file,
      });
      if (!response.ok) {
        throw new PrintJobUploadError(response.status);
      }
    },
    submitPrintJob: (
      request: MessageInitShape<typeof SubmitPrintJobRequestSchema>,
    ) => client.submitPrintJob(request),
    listPrintJobs: (
      request: MessageInitShape<typeof ListPrintJobsRequestSchema>,
    ) => client.listPrintJobs(request),
    getPrintJob: (request: MessageInitShape<typeof GetPrintJobRequestSchema>) =>
      client.getPrintJob(request),
  };
}
