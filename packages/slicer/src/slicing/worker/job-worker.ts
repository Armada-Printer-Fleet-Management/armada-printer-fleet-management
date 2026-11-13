/**
 * The entry point of a job's worker. It takes one request, runs it, reports back, and is then
 * terminated by the page. Each job gets its own worker, so a fresh engine and all its memory go
 * with it.
 *
 *   onmessage(request)  ◀── posted once by run-in-worker.ts
 *        │
 *        ▼
 *   runJob(request, { readText }, report)
 *        │      readText(url): fetch() ── refused on file:// (desktop) ──▶ XMLHttpRequest
 *        │      report(progress) ──────────▶ postMessage { progress }      (no transfer)
 *        │
 *        ├── resolves ──▶ postMessage { done, result }
 *        │                  transfer: gcode, positions, features, layerStarts, layerZ buffers
 *        │                  (moved to the page, so this worker no longer holds them)
 *        │
 *        └── throws ────▶ postMessage { failed, violations }
 *                           SlicerJobError ─▶ its own violations
 *                           anything else  ─▶ one ENGINE_FAILED violation with its message
 */
import { SlicerViolationCode } from '../../gen/print_preparation/validation/v1/violation_pb';
import { SlicerJobError, slicerViolation } from '../../validation/violations';
import { readText } from '../read-file';
import type { SliceResult } from '../types';
import type { JobMessage, JobRequest } from './protocol';
import { runJob } from './run-job';

/** The parts of a dedicated worker's global scope used here; the DOM typings describe a window. */
interface WorkerScope {
  onmessage: ((event: MessageEvent<JobRequest>) => void) | null;
  postMessage(message: JobMessage, transfer: Transferable[]): void;
}

const scope = self as unknown as WorkerScope;

scope.onmessage = (event) => {
  void run(event.data);
};

async function run(request: JobRequest): Promise<void> {
  try {
    const result = await runJob(request, { readText }, (progress) =>
      scope.postMessage({ type: 'progress', progress }, []),
    );
    scope.postMessage({ type: 'done', result }, transferables(result));
  } catch (error: unknown) {
    const violations =
      error instanceof SlicerJobError
        ? error.violations
        : [
            slicerViolation(
              SlicerViolationCode.ENGINE_FAILED,
              `The slicer stopped unexpectedly: ${error instanceof Error ? error.message : String(error)}`,
            ),
          ];
    scope.postMessage({ type: 'failed', violations }, []);
  }
}

/** The result's large buffers move to the page instead of being copied. */
function transferables(result: SliceResult): Transferable[] {
  const { toolpaths } = result;
  return [
    result.gcode.buffer,
    toolpaths.positions.buffer,
    toolpaths.features.buffer,
    toolpaths.layerStarts.buffer,
    toolpaths.layerZ.buffer,
  ].filter((buffer): buffer is ArrayBuffer => buffer instanceof ArrayBuffer);
}
