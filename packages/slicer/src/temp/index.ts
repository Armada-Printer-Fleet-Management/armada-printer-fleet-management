// TEMPORARY: the slicer's actions on the shared vertical slice page, used by both apps. Delete this
// folder, the "./temp" export in package.json and each app's use of it with
// packages/ui-kit/src/temp/.

import { toJson } from '@bufbuild/protobuf';
import type { TempSliceAction, TempSliceOption } from '@armada/ui-kit';
import { SliceSummarySchema } from '../gen/print_preparation/slicing/v1/slice_summary_pb';
import { SlicerViolationSchema } from '../gen/print_preparation/validation/v1/violation_pb';
import { parseGcode, sliceModel } from '../slicing/jobs';
import { readBytes } from '../slicing/read-file';
import { stlBounds } from '../slicing/stl';
import type { SliceResult, SliceSettingsInput } from '../slicing/types';

/** A printer type to slice for, with the bed the fleet is fitted to. */
export interface TempPrinterType {
  model: string;
  bedWidthMm: number;
  bedDepthMm: number;
}

export interface TempSlicerSources<P extends TempSamplePrint> {
  /** The app's base URL, beside which the engine is served. */
  engineBase: string;
  printerTypes: TempPrinterType[];
  sliceSettings(printerType: TempPrinterType): Promise<SliceSettingsInput>;
  /** The bundled Benchy Armada print, shaped as @armada/sample-prints lists it. */
  armada: P | undefined;
  /** Where one of a print's files is served. */
  fileUrl(print: P, file: P['files'][number]): URL;
}

interface TempSamplePrint {
  files: readonly { kind: string }[];
  arrangement?: readonly { xMm: number; yMm: number }[];
}

export function tempSlicerActions<P extends TempSamplePrint>(
  sources: TempSlicerSources<P>,
): TempSliceAction[] {
  const { armada } = sources;
  const placements = armada?.arrangement ?? [{ xMm: 0, yMm: 0 }];
  const fileUrl = (kind: string) => {
    const file = armada?.files.find((candidate) => candidate.kind === kind);
    return armada && file ? sources.fileUrl(armada, file).href : undefined;
  };
  const modelUrl = fileUrl('model');
  const gcodeUrl = fileUrl('gcode');
  const printerOptions: TempSliceOption[] = sources.printerTypes.map(
    (type) => ({
      value: type.model,
      label: `${type.model} (${type.bedWidthMm} × ${type.bedDepthMm} mm)`,
    }),
  );
  return [
    {
      label: 'Slice the Armada',
      fields: [
        { name: 'printer', label: 'Printer type', options: printerOptions },
      ],
      run: async ({ printer = '' }) => {
        const type = sources.printerTypes.find(
          (candidate) => candidate.model === printer,
        );
        if (!type) throw new Error('No printer type is available.');
        if (!modelUrl) throw new Error('The Benchy Armada is not bundled.');
        const model = await readBytes(modelUrl);
        const fitted = fitToBed(model, placements, type);
        if (fitted.length === 0) {
          throw new Error(`Not one Benchy fits the ${type.model}'s bed.`);
        }
        const settings = await sources.sliceSettings(type);
        let peakHeapBytes = 0;
        const started = performance.now();
        const result = await sliceModel(
          {
            models: fitted.map((placement) => ({ model, ...placement })),
            settings,
            engineBase: sources.engineBase,
          },
          {
            onProgress: ({ heapBytes = 0 }) => {
              peakHeapBytes = Math.max(peakHeapBytes, heapBytes);
            },
          },
        );
        return {
          benchies: `${fitted.length} of ${placements.length} fit the bed`,
          seconds: Math.round((performance.now() - started) / 100) / 10,
          peakEngineMemoryMiB: Math.round(peakHeapBytes / 1024 ** 2),
          ...describe(result),
        };
      },
    },
    {
      label: 'Parse sample G-code',
      run: async () => {
        if (!gcodeUrl) throw new Error('No sample G-code is bundled yet.');
        return describe(await parseGcode(await readBytes(gcodeUrl)));
      },
    },
    {
      label: 'Parse a G-code file',
      fields: [{ name: 'gcode', label: 'G-code file', accept: '.gcode' }],
      run: async (_values, files) => {
        const file = files.gcode;
        if (!file) throw new Error('Choose a G-code file first.');
        return describe(await parseGcode(file));
      },
    },
  ];
}

/** The placements whose footprint lies wholly on the bed. */
function fitToBed(
  model: Uint8Array,
  placements: readonly { xMm: number; yMm: number }[],
  type: TempPrinterType,
) {
  const { min, max } = stlBounds(model);
  const halfWidth = (max[0] - min[0]) / 2;
  const halfDepth = (max[1] - min[1]) / 2;
  return placements.filter(
    ({ xMm, yMm }) =>
      Math.abs(xMm) + halfWidth <= type.bedWidthMm / 2 &&
      Math.abs(yMm) + halfDepth <= type.bedDepthMm / 2,
  );
}

function describe(result: SliceResult) {
  return {
    source: result.source,
    gcodeBytes: result.gcode.byteLength,
    segments: result.toolpaths.features.length,
    layers: result.toolpaths.layerStarts.length,
    summary: toJson(SliceSummarySchema, result.summary),
    violations: result.violations.map((violation) =>
      toJson(SlicerViolationSchema, violation),
    ),
  };
}
