// @vitest-environment node
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { SlicerViolationCode } from '../gen/print_preparation/validation/v1/violation_pb';
import { SlicerJobError } from '../validation/violations';
import { runInWorker } from './run-in-worker';
import type { JobMessage, JobRequest } from './worker/protocol';

/** Stands in for the job's worker: the test plays the worker's side of the protocol. */
class FakeWorker {
  static last: FakeWorker | undefined;
  onmessage: ((event: { data: JobMessage }) => void) | null = null;
  onerror: ((event: { message: string }) => void) | null = null;
  terminated = false;

  constructor() {
    FakeWorker.last = this;
  }

  postMessage(): void {}

  terminate(): void {
    this.terminated = true;
  }

  send(message: JobMessage): void {
    this.onmessage?.({ data: message });
  }
}

const REQUEST: JobRequest = {
  kind: 'parse',
  gcode: new Uint8Array(),
  segmentBudget: 1,
};
const MIB = 1024 ** 2;

const worker = () => {
  if (!FakeWorker.last) throw new Error('No worker was started.');
  return FakeWorker.last;
};

beforeEach(() => {
  FakeWorker.last = undefined;
  vi.stubGlobal('Worker', FakeWorker);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

test('a job over its memory budget is stopped as too large to slice', async () => {
  const progress = vi.fn();
  const job = runInWorker(REQUEST, {
    memoryBudgetBytes: 100 * MIB,
    onProgress: progress,
  });

  worker().send({
    type: 'progress',
    progress: { fraction: 0.1, heapBytes: 50 * MIB },
  });
  worker().send({
    type: 'progress',
    progress: { fraction: 0.2, heapBytes: 101 * MIB },
  });

  const error: unknown = await job.catch((caught: unknown) => caught);
  expect(error).toBeInstanceOf(SlicerJobError);
  expect((error as SlicerJobError).violations[0]?.code).toBe(
    SlicerViolationCode.MODEL_TOO_LARGE,
  );
  expect(worker().terminated).toBe(true);
  expect(progress).toHaveBeenCalledTimes(1);
});

test('aborting a job stops its worker', async () => {
  const controller = new AbortController();
  const job = runInWorker(REQUEST, {
    memoryBudgetBytes: 100 * MIB,
    signal: controller.signal,
  });

  controller.abort();

  await expect(job).rejects.toMatchObject({ name: 'AbortError' });
  expect(worker().terminated).toBe(true);
});
