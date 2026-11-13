import { SlicerViolationCode } from '../gen/print_preparation/validation/v1/violation_pb';
import { SlicerJobError, slicerViolation } from '../validation/violations';

export interface MeshBounds {
  min: [number, number, number];
  max: [number, number, number];
}

// The binary STL layout: an 80-byte header, a 32-bit triangle count, then one fixed-size record
// per triangle: its normal, its three vertices (three 32-bit floats each) and a 16-bit attribute.
// All little-endian. Reference: https://en.wikipedia.org/wiki/STL_(file_format)
const HEADER_BYTES = 80;
const COUNT_BYTES = 4;
const FLOAT_BYTES = 4;
const VECTOR_BYTES = 3 * FLOAT_BYTES;
const VERTICES_PER_TRIANGLE = 3;
const ATTRIBUTE_BYTES = 2;
const TRIANGLE_BYTES =
  VECTOR_BYTES + VERTICES_PER_TRIANGLE * VECTOR_BYTES + ATTRIBUTE_BYTES;
const FIRST_TRIANGLE = HEADER_BYTES + COUNT_BYTES;

/** The box an STL's vertices fill, from a binary or text STL. Placing a model on the bed needs it. */
export function stlBounds(data: Uint8Array): MeshBounds {
  const bounds: MeshBounds = {
    min: [Infinity, Infinity, Infinity],
    max: [-Infinity, -Infinity, -Infinity],
  };
  const include = (x: number, y: number, z: number) => {
    bounds.min = [
      Math.min(bounds.min[0], x),
      Math.min(bounds.min[1], y),
      Math.min(bounds.min[2], z),
    ];
    bounds.max = [
      Math.max(bounds.max[0], x),
      Math.max(bounds.max[1], y),
      Math.max(bounds.max[2], z),
    ];
  };

  const view = new DataView(data.buffer, data.byteOffset, data.byteLength);
  const triangles = binaryTriangleCount(view);
  if (triangles !== undefined) {
    for (let triangle = 0; triangle < triangles; triangle++) {
      // Each record starts with the normal; its vertices follow.
      const vertices =
        FIRST_TRIANGLE + triangle * TRIANGLE_BYTES + VECTOR_BYTES;
      for (let vertex = 0; vertex < VERTICES_PER_TRIANGLE; vertex++) {
        const at = vertices + vertex * VECTOR_BYTES;
        include(
          view.getFloat32(at, true),
          view.getFloat32(at + FLOAT_BYTES, true),
          view.getFloat32(at + 2 * FLOAT_BYTES, true),
        );
      }
    }
  } else {
    const text = new TextDecoder().decode(data);
    for (const [, x, y, z] of text.matchAll(
      /vertex\s+(\S+)\s+(\S+)\s+(\S+)/g,
    )) {
      include(Number(x), Number(y), Number(z));
    }
  }

  if (
    !bounds.min.every(Number.isFinite) ||
    !bounds.max.every(Number.isFinite)
  ) {
    throw new SlicerJobError([
      slicerViolation(
        SlicerViolationCode.UNREADABLE_MODEL,
        'This file is not a readable STL or OBJ model. Export it again as STL or OBJ and try once more.',
      ),
    ]);
  }
  return bounds;
}

/** The triangle count when the file is a binary STL, which its exact size gives away; else none. */
function binaryTriangleCount(view: DataView): number | undefined {
  if (view.byteLength < FIRST_TRIANGLE) {
    return undefined;
  }
  const triangles = view.getUint32(HEADER_BYTES, true);
  return view.byteLength === FIRST_TRIANGLE + triangles * TRIANGLE_BYTES
    ? triangles
    : undefined;
}
