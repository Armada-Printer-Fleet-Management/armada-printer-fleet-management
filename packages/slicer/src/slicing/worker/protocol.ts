import type { SlicerViolation } from '../../gen/print_preparation/validation/v1/violation_pb';
import type { SliceProgress, SliceResult } from '../types';

export type { JobRequest } from './run-job';

/** What a job's worker sends back to the page. */
export type JobMessage =
  | { type: 'progress'; progress: SliceProgress }
  | { type: 'done'; result: SliceResult }
  | { type: 'failed'; violations: SlicerViolation[] };
