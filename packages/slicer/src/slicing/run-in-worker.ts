/**
 * Runs one job in its own worker, from the page. The worker is created for the job and terminated
 * the moment it settles, so each slice gets a fresh engine and gives all its memory back.
 *
 *   page (this file)                              worker (worker/job-worker.ts)
 *   ────────────────                              ─────────────────────────────
 *   new Worker(job-worker.ts) ───────────────────▶ started
 *   postMessage(request) ────────────────────────▶ runJob(request)
 *                                                      │
 *   onProgress(progress) ◀──── { progress } ──────────┤ many times
 *     heapBytes > memory budget?                      │
 *       yes ─▶ terminate, reject MODEL_TOO_LARGE      │
 *                                                      │
 *   resolve(result) ◀──────── { done, result } ───────┤ large buffers transferred, not copied
 *   reject(SlicerJobError) ◀── { failed, violations } ┘
 *   reject(AbortError) ◀── signal aborted: terminate
 *        │
 *        ▼
 *   terminate the worker, whatever happened
 */
import { SlicerViolationCode } from '../gen/print_preparation/validation/v1/violation_pb';
import {
  SlicerJobError,
  slicerViolation,
  TOO_LARGE_TO_SLICE,
} from '../validation/violations';
import type { JobOptions, SliceResult } from './types';
import type { JobMessage, JobRequest } from './worker/protocol';

const GIB = 1024 ** 3;
// The engine can grow to 4 GiB; stopping short of it leaves the browser room to stay responsive.
const MAX_MEMORY_BUDGET_BYTES = 3.5 * GIB;
// Where the browser says how much memory the device has, a job may use at most half of it.
const DEVICE_MEMORY_SHARE = 0.5;

export interface WorkerJobOptions extends JobOptions {
  /** Stop the job once the engine uses more than this. */
  memoryBudgetBytes?: number;
}

export function runInWorker(
  request: JobRequest,
  options: WorkerJobOptions = {},
): Promise<SliceResult> {
  const budget = options.memoryBudgetBytes ?? defaultMemoryBudget();
  return new Promise((resolve, reject) => {
    if (options.signal?.aborted) {
      reject(abortError());
      return;
    }
    const worker = new Worker(
      new URL('./worker/job-worker.ts', import.meta.url),
      {
        type: 'module',
      },
    );
    const settle = () => {
      worker.terminate();
      options.signal?.removeEventListener('abort', onAbort);
    };
    const onAbort = () => {
      settle();
      reject(abortError());
    };
    options.signal?.addEventListener('abort', onAbort, { once: true });

    worker.onmessage = (event: MessageEvent<JobMessage>) => {
      const message = event.data;
      switch (message.type) {
        case 'progress':
          if ((message.progress.heapBytes ?? 0) > budget) {
            settle();
            reject(
              new SlicerJobError([
                slicerViolation(
                  SlicerViolationCode.MODEL_TOO_LARGE,
                  TOO_LARGE_TO_SLICE,
                ),
              ]),
            );
            return;
          }
          options.onProgress?.(message.progress);
          break;
        case 'done':
          settle();
          resolve(message.result);
          break;
        case 'failed':
          settle();
          reject(new SlicerJobError(message.violations));
          break;
      }
    };
    worker.onerror = (event) => {
      settle();
      reject(
        new SlicerJobError([
          slicerViolation(
            SlicerViolationCode.ENGINE_FAILED,
            `The slicer could not start: ${event.message || 'the worker failed to load'}.`,
          ),
        ]),
      );
    };
    worker.postMessage(request);
  });
}

function defaultMemoryBudget(): number {
  // navigator.deviceMemory is in gibibytes and not in every browser's typings.
  const deviceGib = (navigator as { deviceMemory?: number }).deviceMemory;
  return deviceGib
    ? Math.min(MAX_MEMORY_BUDGET_BYTES, deviceGib * GIB * DEVICE_MEMORY_SHARE)
    : MAX_MEMORY_BUDGET_BYTES;
}

function abortError(): DOMException {
  return new DOMException('The slicer job was cancelled.', 'AbortError');
}
