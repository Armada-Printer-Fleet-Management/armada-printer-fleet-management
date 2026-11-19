import {
  SLICER_DEFINITION_FILES,
  slicerEngineUrl,
} from '@armada/slicer-engine';
import { runInWorker, type WorkerJobOptions } from './run-in-worker';
import type { PlacedModel, SliceResult, SliceSettingsInput } from './types';

/** The most moves a print may have before it is too large to show: 10 million segments is about
 * 250 MB of toolpaths in the browser. */
export const DEFAULT_SEGMENT_BUDGET = 10_000_000;

export interface SliceJobOptions extends WorkerJobOptions {
  segmentBudget?: number;
}

export interface SliceModelInput {
  /** The models to slice together, each placed on the bed. */
  models: PlacedModel[];
  /** The settings the server built for the printer type. */
  settings: SliceSettingsInput;
  /** The app's base URL, beside which the engine is served. */
  engineBase: string;
}

/** Slices models into G-code in a fresh worker, then reads it into toolpaths and a summary. */
export function sliceModel(
  input: SliceModelInput,
  options: SliceJobOptions = {},
): Promise<SliceResult> {
  const engineUrl = slicerEngineUrl(input.engineBase);
  return runInWorker(
    {
      kind: 'slice',
      engineUrl: engineUrl.href,
      definitionUrls: Object.fromEntries(
        SLICER_DEFINITION_FILES.map((name) => [
          name,
          new URL(name, engineUrl).href,
        ]),
      ),
      models: input.models.map((placed) => ({
        data: placed.model,
        xMm: placed.xMm ?? 0,
        yMm: placed.yMm ?? 0,
      })),
      machineSettings: { ...input.settings.machineSettings },
      extruderSettings: { ...input.settings.extruderSettings },
      segmentBudget: options.segmentBudget ?? DEFAULT_SEGMENT_BUDGET,
    },
    options,
  );
}

/** Reads G-code a student already sliced, such as one too large to slice in the browser. */
export function parseGcode(
  gcode: Blob | Uint8Array,
  options: SliceJobOptions = {},
): Promise<SliceResult> {
  return runInWorker(
    {
      kind: 'parse',
      gcode,
      segmentBudget: options.segmentBudget ?? DEFAULT_SEGMENT_BUDGET,
    },
    options,
  );
}
