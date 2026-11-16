import { createApiClient, PrintJobStatus } from '@armada/api-client';
import { FileType } from '@armada/api-client/gen/content_asset/v1/file_pb';
import {
  CreatePrintJobResponseSchema,
  CreatePrintJobUploadResponseSchema,
  SubmitPrintJobResponseSchema,
} from '@armada/api-client/gen/server/v1/print_job_service_pb';
import { create } from '@bufbuild/protobuf';
import { describe, expect, it, vi } from 'vitest';

import {
  PrintSubmission,
  validateFile,
  type SubmissionState,
} from './print-submission';

function setup(file = new File(['abc'], 'part.gcode')) {
  const api = createApiClient().printJobs;
  const id = { value: 'job-id' };
  const createJob = vi.spyOn(api, 'createPrintJob').mockResolvedValue(
    create(CreatePrintJobResponseSchema, {
      printJob: { id, status: PrintJobStatus.DRAFT },
    }),
  );
  const createUpload = vi.spyOn(api, 'createPrintJobUpload').mockResolvedValue(
    create(CreatePrintJobUploadResponseSchema, {
      slot: { uploadUrl: 'https://storage.example/upload?token=secret' },
    }),
  );
  const upload = vi
    .spyOn(api, 'uploadPrintJobFile')
    .mockResolvedValue(undefined);
  const submit = vi.spyOn(api, 'submitPrintJob').mockResolvedValue(
    create(SubmitPrintJobResponseSchema, {
      printJob: { id, status: PrintJobStatus.SUBMITTED },
    }),
  );
  const states: SubmissionState[] = [];
  const submission = new PrintSubmission(api, file, 'notes', (state) =>
    states.push(state),
  );
  return {
    api,
    file,
    submission,
    states,
    createJob,
    createUpload,
    upload,
    submit,
  };
}

describe('print file validation', () => {
  it('accepts supported, nonempty files and rejects other formats and empty files', () => {
    expect(validateFile(new File(['x'], 'part.gcode'))).toBeUndefined();
    expect(validateFile(new File(['x'], 'part.CGCODE'))).toBeUndefined();
    expect(validateFile(new File(['x'], 'part.stl'))).toBeDefined();
    expect(validateFile(new File([], 'part.gcode'))).toBeDefined();
  });

  it('rejects invalid FAT32-compatible filenames and names over 255 characters', () => {
    expect(validateFile(new File(['x'], 'bad:name.gcode'))).toBeDefined();
    expect(validateFile(new File(['x'], 'CON.gcode'))).toBeDefined();
    expect(
      validateFile(new File(['x'], `${'a'.repeat(250)}.gcode`)),
    ).toBeDefined();
  });
});

describe('print submission', () => {
  it('creates a draft, sends exact metadata, uploads bytes, then submits', async () => {
    const {
      submission,
      file,
      createJob,
      createUpload,
      upload,
      submit,
      states,
    } = setup();
    await submission.start();

    expect(createJob).toHaveBeenCalledWith({ userNotes: 'notes' });
    const request = createUpload.mock.calls[0]?.[0];
    expect(request?.printJobId?.value).toBe('job-id');
    expect(request?.metadata).toEqual({
      filename: 'part.gcode',
      sizeBytes: 3n,
      sha256:
        'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad',
      fileType: FileType.GCODE,
    });
    expect(upload.mock.calls[0]?.[0].uploadUrl).toBe(
      'https://storage.example/upload?token=secret',
    );
    expect(upload.mock.calls[0]?.[1]).toBe(file);
    expect(createJob.mock.invocationCallOrder[0]).toBeLessThan(
      createUpload.mock.invocationCallOrder[0] ?? 0,
    );
    expect(createUpload.mock.invocationCallOrder[0]).toBeLessThan(
      upload.mock.invocationCallOrder[0] ?? 0,
    );
    expect(upload.mock.invocationCallOrder[0]).toBeLessThan(
      submit.mock.invocationCallOrder[0] ?? 0,
    );
    expect(states.at(-1)).toEqual({ phase: 'success' });

    const compressed = setup(new File(['abc'], 'part.cgcode'));
    await compressed.submission.start();
    expect(compressed.createUpload.mock.calls[0]?.[0].metadata?.fileType).toBe(
      FileType.CGCODE,
    );
  });

  it('retries a failed upload on the same draft', async () => {
    const { submission, createJob, createUpload, upload, submit, states } =
      setup();
    upload.mockRejectedValueOnce(new Error('network failure'));
    await submission.start();
    expect(states.at(-1)?.phase).toBe('failed-upload');
    await submission.retry();
    expect(createJob).toHaveBeenCalledTimes(1);
    expect(createUpload).toHaveBeenCalledTimes(2);
    expect(submit).toHaveBeenCalledTimes(1);
    expect(states.at(-1)?.phase).toBe('success');
  });

  it('does not resubmit or claim success when submission status cannot be determined', async () => {
    const { api, submission, submit, states } = setup();
    submit.mockRejectedValue(new Error('connection lost'));
    const getJob = vi
      .spyOn(api, 'getPrintJob')
      .mockRejectedValue(new Error('connection lost'));
    await submission.start();
    expect(states.at(-1)?.phase).toBe('unknown');
    await submission.retry();
    expect(getJob).toHaveBeenCalledTimes(2);
    expect(submit).toHaveBeenCalledTimes(1);
    expect(states.at(-1)?.phase).toBe('unknown');
  });
});
