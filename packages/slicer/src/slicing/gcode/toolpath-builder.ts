import { SlicerViolationCode } from '../../gen/print_preparation/validation/v1/violation_pb';
import { SlicerJobError, slicerViolation } from '../../validation/violations';
import type { Toolpaths } from '../types';

const FLOATS_PER_SEGMENT = 6;
const INITIAL_SEGMENTS = 1 << 16;

/** Packs moves into the typed arrays a renderer draws from, growing them as it goes. */
export class ToolpathBuilder {
  private positions = new Float32Array(INITIAL_SEGMENTS * FLOATS_PER_SEGMENT);
  private features = new Uint8Array(INITIAL_SEGMENTS);
  private readonly layerStarts: number[] = [];
  private readonly layerZ: number[] = [];
  private count = 0;

  constructor(private readonly segmentBudget: number) {}

  get layerCount(): number {
    return this.layerStarts.length;
  }

  startLayer(z: number): void {
    this.layerStarts.push(this.count);
    this.layerZ.push(z);
  }

  add(
    from: readonly [number, number, number],
    to: readonly [number, number, number],
    feature: number,
  ): void {
    if (this.count >= this.segmentBudget) {
      throw new SlicerJobError([
        slicerViolation(
          SlicerViolationCode.GCODE_TOO_LARGE,
          `This G-code has more than ${this.segmentBudget.toLocaleString()} moves, too many to show. Slice it with fewer details, such as a larger layer height.`,
        ),
      ]);
    }
    if (this.count === this.features.length) {
      this.grow();
    }
    const at = this.count * FLOATS_PER_SEGMENT;
    this.positions.set([from[0], from[1], from[2], to[0], to[1], to[2]], at);
    this.features[this.count] = feature;
    this.count++;
  }

  build(): Toolpaths {
    return {
      positions: this.positions.slice(0, this.count * FLOATS_PER_SEGMENT),
      features: this.features.slice(0, this.count),
      layerStarts: Uint32Array.from(this.layerStarts),
      layerZ: Float32Array.from(this.layerZ),
    };
  }

  private grow(): void {
    const segments = Math.min(this.features.length * 2, this.segmentBudget);
    const positions = new Float32Array(segments * FLOATS_PER_SEGMENT);
    positions.set(this.positions);
    const features = new Uint8Array(segments);
    features.set(this.features);
    this.positions = positions;
    this.features = features;
  }
}
