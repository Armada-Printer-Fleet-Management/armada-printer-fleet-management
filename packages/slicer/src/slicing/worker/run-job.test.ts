// @vitest-environment node
import { readFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { SLICER_DEFINITION_FILES } from '@armada/slicer-engine';
import { expect, test } from 'vitest';
import { runJob } from './run-job';

const ENGINE_DIR = fileURLToPath(
  new URL('../../../../slicer-engine/gen/', import.meta.url),
);
const BRIDGE = new URL(
  '../../../../sample-prints/test/bridge-obj/bridge.obj',
  import.meta.url,
);
const BED_MM = { width: 250, depth: 210 };
const NOZZLE_MM = '0.4';

// The engine never evaluates a definition's formulas, so each line width the server would derive
// from the nozzle is given here, as the server's slice settings give it.
const LINE_WIDTHS = [
  'line_width',
  'wall_line_width',
  'wall_line_width_0',
  'wall_line_width_x',
  'skin_line_width',
  'roofing_line_width',
  'flooring_line_width',
  'infill_line_width',
  'skirt_brim_line_width',
  'support_line_width',
  'support_interface_line_width',
  'support_roof_line_width',
  'support_bottom_line_width',
  'prime_tower_line_width',
];

test('slices an OBJ model into G-code centred on the bed', async () => {
  const result = await runJob(
    {
      kind: 'slice',
      engineUrl: pathToFileURL(`${ENGINE_DIR}CuraEngine.js`).href,
      definitionUrls: Object.fromEntries(
        SLICER_DEFINITION_FILES.map((name) => [name, `${ENGINE_DIR}${name}`]),
      ),
      models: [{ data: new Uint8Array(readFileSync(BRIDGE)), xMm: 0, yMm: 0 }],
      machineSettings: {
        machine_width: String(BED_MM.width),
        machine_depth: String(BED_MM.depth),
        machine_height: '220',
      },
      extruderSettings: {
        machine_nozzle_size: NOZZLE_MM,
        material_diameter: '1.75',
        ...Object.fromEntries(LINE_WIDTHS.map((name) => [name, NOZZLE_MM])),
      },
      segmentBudget: 10_000_000,
    },
    { readText: (path) => Promise.resolve(readFileSync(path, 'utf8')) },
    () => undefined,
  );

  const { summary } = result;
  expect(result.source).toBe('engine');
  expect(summary.slicer).toMatch(/^Cura_SteamEngine /);
  // The bridge is 8 mm tall.
  expect(summary.bounds?.max?.z).toBeLessThanOrEqual(8.0001);
  expect(summary.layerCount).toBeGreaterThan(20);
  // Its 50 x 10 mm footprint, centred, with room for the skirt around it.
  const centreX =
    ((summary.bounds?.min?.x ?? 0) + (summary.bounds?.max?.x ?? 0)) / 2;
  const centreY =
    ((summary.bounds?.min?.y ?? 0) + (summary.bounds?.max?.y ?? 0)) / 2;
  expect(centreX).toBeCloseTo(BED_MM.width / 2, 0);
  expect(centreY).toBeCloseTo(BED_MM.depth / 2, 0);
}, 60_000);
