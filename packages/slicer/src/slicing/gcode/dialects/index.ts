import { cura } from './cura';
import type { GcodeDialect } from './dialect';

export type { GcodeDialect } from './dialect';

/** Every slicer whose G-code annotations are understood. Add a dialect here to support another. */
const DIALECTS: readonly GcodeDialect[] = [cura];

export interface SupportedSlicer {
  id: string;
  name: string;
}

/** The slicers whose G-code is read feature by feature. Any other G-code still loads, but only as
 * extrusion and travel. */
export function supportedSlicers(): SupportedSlicer[] {
  return DIALECTS.map(({ id, name }) => ({ id, name }));
}

export function detectDialect(header: string): GcodeDialect | undefined {
  return DIALECTS.find((dialect) => dialect.detects(header));
}
