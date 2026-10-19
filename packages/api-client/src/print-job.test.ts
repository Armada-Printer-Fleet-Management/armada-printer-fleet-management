import { create } from '@bufbuild/protobuf';
import { describe, expect, it, vi } from 'vitest';
import { PrintJobUploadError } from './errors';
import { createPrintJobApi } from './print-job';
import {
  CreatePrintJobResponseSchema,
  CreatePrintJobUploadResponseSchema,
  GetPrintJobResponseSchema,
  ListPrintJobsResponseSchema,
  PrintJobService,
  SubmitPrintJobResponseSchema,
} from './gen/server/v1/print_job_service_pb';
import { FileUploadSlotSchema } from './gen/file/v1/file_upload_pb';

function createRpcClient() {
  return {
    createPrintJob: () => Promise.resolve(create(CreatePrintJobResponseSchema)),
    createPrintJobUpload: () =>
      Promise.resolve(create(CreatePrintJobUploadResponseSchema)),
    submitPrintJob: () => Promise.resolve(create(SubmitPrintJobResponseSchema)),
    listPrintJobs: () => Promise.resolve(create(ListPrintJobsResponseSchema)),
    getPrintJob: () => Promise.resolve(create(GetPrintJobResponseSchema)),
  };
}

describe('createPrintJobApi', () => {
  it('forwards generated RPC request shapes to the matching methods', async () => {
    const client = {
      createPrintJob: vi.fn(() =>
        Promise.resolve(create(CreatePrintJobResponseSchema)),
      ),
      createPrintJobUpload: vi.fn(() =>
        Promise.resolve(create(CreatePrintJobUploadResponseSchema)),
      ),
      submitPrintJob: vi.fn(() =>
        Promise.resolve(create(SubmitPrintJobResponseSchema)),
      ),
      listPrintJobs: vi.fn(() =>
        Promise.resolve(create(ListPrintJobsResponseSchema)),
      ),
      getPrintJob: vi.fn(() =>
        Promise.resolve(create(GetPrintJobResponseSchema)),
      ),
    } satisfies Pick<
      import('@connectrpc/connect').Client<typeof PrintJobService>,
      | 'createPrintJob'
      | 'createPrintJobUpload'
      | 'submitPrintJob'
      | 'listPrintJobs'
      | 'getPrintJob'
    >;
    const api = createPrintJobApi(client, vi.fn());
    const createRequest = { userNotes: 'A test job' };
    const uploadRequest = {
      printJobId: { value: 'job-id' },
      metadata: {
        filename: 'part.gcode',
        sizeBytes: 1n,
        sha256: 'a'.repeat(64),
        fileType: 1,
      },
    };
    const submitRequest = { printJobId: { value: 'job-id' } };
    const listRequest = { page: { pageSize: 10, pageToken: 'next' } };
    const getRequest = { printJobId: { value: 'job-id' } };

    await api.createPrintJob(createRequest);
    await api.createPrintJobUpload(uploadRequest);
    await api.submitPrintJob(submitRequest);
    await api.listPrintJobs(listRequest);
    await api.getPrintJob(getRequest);

    expect(client.createPrintJob).toHaveBeenCalledWith(createRequest);
    expect(client.createPrintJobUpload).toHaveBeenCalledWith(uploadRequest);
    expect(client.submitPrintJob).toHaveBeenCalledWith(submitRequest);
    expect(client.listPrintJobs).toHaveBeenCalledWith(listRequest);
    expect(client.getPrintJob).toHaveBeenCalledWith(getRequest);
  });

  it('PUTs the raw file bytes to the upload slot URL', async () => {
    const uploadFetch = vi.fn<typeof globalThis.fetch>(() =>
      Promise.resolve(new Response(null, { status: 204 })),
    );
    const api = createPrintJobApi(createRpcClient(), uploadFetch);
    const slot = create(FileUploadSlotSchema, {
      uploadUrl: 'https://storage.example/upload?signature=secret',
    });
    const file = new Blob(['GCODE']);

    await api.uploadPrintJobFile(slot, file);

    expect(uploadFetch).toHaveBeenCalledWith(slot.uploadUrl, {
      method: 'PUT',
      body: file,
    });
  });

  it('reports upload HTTP failures without exposing the upload URL', async () => {
    const uploadFetch = vi.fn<typeof globalThis.fetch>(() =>
      Promise.resolve(new Response(null, { status: 403 })),
    );
    const api = createPrintJobApi(createRpcClient(), uploadFetch);
    const secretUrl = 'https://storage.example/upload?signature=secret';
    const slot = create(FileUploadSlotSchema, { uploadUrl: secretUrl });

    const upload = api.uploadPrintJobFile(slot, new Blob(['GCODE']));

    await expect(upload).rejects.toMatchObject({
      name: PrintJobUploadError.name,
      status: 403,
    });
    await expect(upload).rejects.not.toThrow(secretUrl);
  });
});
