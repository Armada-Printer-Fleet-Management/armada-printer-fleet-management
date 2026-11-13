import type { SliceSummary } from '../gen/print_preparation/slicing/v1/slice_summary_pb';
import type { SlicerViolation } from '../gen/print_preparation/validation/v1/violation_pb';

/** Engine setting names and values, as the engine reads them. */
export type Settings = Record<string, string>;

/** The engine settings to slice with, as the server built them: print_preparation.slicing.v1
 * SliceSettings. Either app passes its own generated message straight in. */
export interface SliceSettingsInput {
  machineSettings: Readonly<Settings>;
  extruderSettings: Readonly<Settings>;
}

/** One model on the bed: an STL, its footprint centred this far from the bed centre. */
export interface PlacedModel {
  model: Blob | Uint8Array;
  xMm?: number;
  yMm?: number;
}

/**
 * Every move of a print, ready to draw. Segment i runs from positions[6i..6i+2] to
 * positions[6i+3..6i+5] and is features[i], a ToolpathFeature. Layer n's segments start at
 * layerStarts[n] and sit at height layerZ[n].
 */
export interface Toolpaths {
  positions: Float32Array;
  features: Uint8Array;
  layerStarts: Uint32Array;
  layerZ: Float32Array;
}

/** The same result whether the print was sliced here or arrived as G-code. */
export interface SliceResult {
  source: 'engine' | 'gcode';
  gcode: Uint8Array;
  /** Computed from the G-code, so it means the same for both sources. Advisory: a server
   * recomputes it from the G-code rather than trusting a client. */
  summary: SliceSummary;
  toolpaths: Toolpaths;
  /** Problems that did not stop the job, such as engine warnings. */
  violations: SlicerViolation[];
  /** The engine's own report of a slice it made, as it gave it. */
  engineReport?: unknown;
}

export interface SliceProgress {
  /** 0 to 1. */
  fraction: number;
  /** The engine's memory in use, while slicing. */
  heapBytes?: number;
}

export interface JobOptions {
  signal?: AbortSignal;
  onProgress?: (progress: SliceProgress) => void;
}
