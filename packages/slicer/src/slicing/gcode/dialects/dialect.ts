import type { ToolpathFeature } from '../../../gen/print_preparation/slicing/v1/slice_summary_pb';

/**
 * How one slicer annotates its G-code. Comments are passed without their leading ';'. A dialect
 * maps them onto the slicer-independent ToolpathFeature list, so nothing past the parser knows
 * which slicer made a file.
 */
export interface GcodeDialect {
  id: string;
  name: string;
  /** Whether the file's opening comment lines are this slicer's. */
  detects(header: string): boolean;
  /** The slicer and its version, as the file names them. */
  slicer(header: string): string;
  /** The feature the moves after this comment draw, if the comment names one. */
  feature(comment: string): ToolpathFeature | undefined;
  /** Whether this comment starts a new layer. */
  startsLayer(comment: string): boolean;
  /** The total print time the header states, in seconds. */
  printTimeSeconds(header: string): number | undefined;
}
