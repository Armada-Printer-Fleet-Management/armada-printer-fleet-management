// The public API of @armada/slicer. React lives in './react' only, so the worker bundle never pulls
// React in.
export {
  DEFAULT_SEGMENT_BUDGET,
  parseGcode,
  sliceModel,
  type SliceJobOptions,
  type SliceModelInput,
} from './slicing/jobs';
export {
  supportedSlicers,
  type SupportedSlicer,
} from './slicing/gcode/dialects';
export type {
  PlacedModel,
  SliceProgress,
  SliceResult,
  SliceSettingsInput,
  Toolpaths,
} from './slicing/types';
export { SlicerJobError, SlicerViolationCode } from './validation/violations';
export { ToolpathFeature } from './gen/print_preparation/slicing/v1/slice_summary_pb';
export type { SliceSummary } from './gen/print_preparation/slicing/v1/slice_summary_pb';
export type { SlicerViolation } from './gen/print_preparation/validation/v1/violation_pb';
export { ViolationSeverity } from './gen/common/v1/violation_pb';
