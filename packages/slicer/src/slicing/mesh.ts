import { SlicerViolationCode } from '../gen/print_preparation/validation/v1/violation_pb';
import { SlicerJobError, slicerViolation } from '../validation/violations';
import { type MeshBounds, stlBounds } from './stl';

/** The model formats the engine loads. It chooses its reader by the file's extension. */
export type MeshFormat = 'stl' | 'obj';

const SNIFF_BYTES = 64 * 1024;
// A vertex line and its x, y and z: "v 75.000000 84.500000 8.000000" gives 75, 84.5 and 8.
// "vn" (normal) and "vt" (texture) lines do not match.
const OBJ_VERTEX = /^v\s+(\S+)\s+(\S+)\s+(\S+)/gm;

/** OBJ when vertex and face lines appear near the start; anything else is read as STL. */
export function meshFormat(data: Uint8Array): MeshFormat {
  const head = new TextDecoder().decode(data.subarray(0, SNIFF_BYTES));
  return /^v\s/m.test(head) && /^f\s/m.test(head) ? 'obj' : 'stl';
}

/** The box a model's vertices fill. Placing a model on the bed needs it. */
export function meshBounds(data: Uint8Array, format: MeshFormat): MeshBounds {
  return format === 'obj' ? objBounds(data) : stlBounds(data);
}

// Reference: https://paulbourke.net/dataformats/obj/
function objBounds(data: Uint8Array): MeshBounds {
  const min: [number, number, number] = [Infinity, Infinity, Infinity];
  const max: [number, number, number] = [-Infinity, -Infinity, -Infinity];
  for (const [, ...coordinates] of new TextDecoder()
    .decode(data)
    .matchAll(OBJ_VERTEX)) {
    coordinates.forEach((text, axis) => {
      const value = Number(text);
      min[axis] = Math.min(min[axis] ?? Infinity, value);
      max[axis] = Math.max(max[axis] ?? -Infinity, value);
    });
  }
  if (![...min, ...max].every(Number.isFinite)) {
    throw new SlicerJobError([
      slicerViolation(
        SlicerViolationCode.UNREADABLE_MODEL,
        'This file is not a readable OBJ model. Export it again as OBJ or STL and try once more.',
      ),
    ]);
  }
  return { min, max };
}
