import { create } from '@bufbuild/protobuf';
import {
  ViolationSchema,
  ViolationSeverity,
} from '../gen/common/v1/violation_pb';
import {
  type SlicerViolation,
  SlicerViolationCode,
  SlicerViolationSchema,
} from '../gen/print_preparation/validation/v1/violation_pb';

export function slicerViolation(
  code: SlicerViolationCode,
  message: string,
  severity: ViolationSeverity = ViolationSeverity.ERROR,
): SlicerViolation {
  return create(SlicerViolationSchema, {
    code,
    violation: create(ViolationSchema, { severity, message }),
  });
}

/** A job that could not finish. Its violations say why, in words a person can act on. */
export class SlicerJobError extends Error {
  constructor(readonly violations: SlicerViolation[]) {
    super(violations.map((each) => each.violation?.message).join(' '));
    this.name = 'SlicerJobError';
  }
}

export const TOO_LARGE_TO_SLICE =
  'This model is too large to slice in the browser. Slice it on your computer and upload the G-code instead.';

export { SlicerViolationCode };
