// @vitest-environment node
import { readFileSync } from 'node:fs';
import { toJson } from '@bufbuild/protobuf';
import { describe, expect, test } from 'vitest';
import {
  type SliceSummary,
  SliceSummarySchema,
  ToolpathFeature,
} from '../../gen/print_preparation/slicing/v1/slice_summary_pb';
import { SlicerViolationCode } from '../../gen/print_preparation/validation/v1/violation_pb';
import { SlicerJobError } from '../../validation/violations';
import { parseGcodeText } from './parse';

const BUDGET = 10_000_000;
const TEST_PRINTS = new URL('../../../../sample-prints/test/', import.meta.url);

const testFile = (name: string) =>
  readFileSync(new URL(`./test-gcode/${name}`, import.meta.url), 'utf8');

const distance = (summary: SliceSummary, feature: ToolpathFeature) =>
  summary.featureStats.find((stat) => stat.feature === feature)?.distanceMm;

/** Rounded to a micrometre, so float noise in the inputs does not fail an exact comparison. */
const rounded = (values: Iterable<number>) =>
  [...values].map((value) => Math.round(value * 1000) / 1000);

/** The bounds as [min x, y, z, max x, y, z], rounded. */
const corners = ({ bounds }: SliceSummary) =>
  rounded([
    bounds?.min?.x ?? NaN,
    bounds?.min?.y ?? NaN,
    bounds?.min?.z ?? NaN,
    bounds?.max?.x ?? NaN,
    bounds?.max?.y ?? NaN,
    bounds?.max?.z ?? NaN,
  ]);

const seconds = (summary: SliceSummary) =>
  Number(summary.printTime?.seconds ?? 0) +
  (summary.printTime?.nanos ?? 0) / 1e9;

async function violationCode(parsing: Promise<unknown>) {
  const error: unknown = await parsing.catch((caught: unknown) => caught);
  expect(error).toBeInstanceOf(SlicerJobError);
  return (error as SlicerJobError).violations[0]?.code;
}

describe('Cura G-code', () => {
  test('reads layers, features, filament and bounds, and takes the time from the header', async () => {
    const { summary, toolpaths } = await parseGcodeText(
      [testFile('cura-two-layers.gcode')],
      {
        segmentBudget: BUDGET,
      },
    );

    expect(summary.slicer).toBe('Cura_SteamEngine 5.13.0');
    expect(summary.layerCount).toBe(2);
    expect(rounded(toolpaths.layerZ)).toEqual([0.2, 0.4]);
    expect(seconds(summary)).toBe(95);
    // The retraction and the prime that follows it cancel out.
    expect(summary.filamentLengthMm).toBeCloseTo(6);
    expect(corners(summary)).toEqual([10, 10, 0.2, 20, 20, 0.4]);
    expect(distance(summary, ToolpathFeature.SKIRT_BRIM)).toBeCloseTo(20);
    expect(distance(summary, ToolpathFeature.OUTER_WALL)).toBeCloseTo(20);
    expect(distance(summary, ToolpathFeature.INFILL)).toBeCloseTo(
      Math.hypot(6, 6),
    );
    expect(distance(summary, ToolpathFeature.INNER_WALL)).toBeCloseTo(10);
    expect(toolpaths.features).toHaveLength(9);
  });
});

describe('G-code from a slicer without a dialect', () => {
  test('starts layers at new heights and estimates the time from the feed rates', async () => {
    const { summary, toolpaths } = await parseGcodeText(
      [testFile('unknown-slicer.gcode')],
      {
        segmentBudget: BUDGET,
      },
    );

    expect(summary.slicer).toBe('ExampleSlicer 2.9.1');
    expect(summary.layerCount).toBe(2);
    expect(rounded(toolpaths.layerZ)).toEqual([0.3, 0.6]);
    expect(distance(summary, ToolpathFeature.EXTRUSION_UNKNOWN)).toBeCloseTo(
      120,
    );
    expect(distance(summary, ToolpathFeature.TRAVEL)).toBeCloseTo(0.6);
    expect(summary.filamentLengthMm).toBeCloseTo(4.8);
    // 120 mm at 30 mm/s, plus two 0.3 mm lifts at 12 mm/s.
    expect(seconds(summary)).toBeCloseTo(4.05);
  });

  test('follows inches, relative moves, relative extrusion, resets and arcs', async () => {
    const { summary } = await parseGcodeText(
      [testFile('modes-and-units.gcode')],
      {
        segmentBudget: BUDGET,
      },
    );

    expect(summary.layerCount).toBe(1);
    expect(distance(summary, ToolpathFeature.EXTRUSION_UNKNOWN)).toBeCloseTo(
      4 * 25.4,
    );
    expect(summary.filamentLengthMm).toBeCloseTo(2 * 1.016 + 1 + 0.5);
    expect(corners(summary)).toEqual([0, 0, 0.254, 25.4, 25.4, 0.254]);
  });
});

describe('input that cannot be shown', () => {
  test.each([
    ['an empty file', ''],
    [
      'a model uploaded instead of its G-code',
      readFileSync(new URL('bridge-obj/bridge.obj', TEST_PRINTS), 'utf8'),
    ],
    [
      'a binary file',
      new TextDecoder().decode(
        readFileSync(
          new URL('voron-cube/Voron_Design_Cube_v7.stl', TEST_PRINTS),
        ),
      ),
    ],
  ])('%s is unreadable G-code', async (_name, text) => {
    expect(
      await violationCode(parseGcodeText([text], { segmentBudget: BUDGET })),
    ).toBe(SlicerViolationCode.UNREADABLE_GCODE);
  });

  test('G-code over the segment budget is too large', async () => {
    expect(
      await violationCode(
        parseGcodeText([testFile('cura-two-layers.gcode')], {
          segmentBudget: 3,
        }),
      ),
    ).toBe(SlicerViolationCode.GCODE_TOO_LARGE);
  });

  test('a line split across two chunks reads the same as a whole file', async () => {
    const text = testFile('cura-two-layers.gcode');
    const chunks = text.match(/[\s\S]{1,7}/g) ?? [];
    const whole = await parseGcodeText([text], { segmentBudget: BUDGET });
    const split = await parseGcodeText(chunks, { segmentBudget: BUDGET });

    expect(toJson(SliceSummarySchema, split.summary)).toEqual(
      toJson(SliceSummarySchema, whole.summary),
    );
  });
});

describe('the G-code test prints', () => {
  test.each([
    ['benchy-mk4s', '3DBenchy_MK4S.gcode'],
    ['voron-cube', 'Voron_Design_Cube_v7_MK4S.gcode'],
    ['extruder-idler', 'extruder_idler_MK4S.gcode'],
  ])('%s parses to its expected summary', async (print, gcode) => {
    const text = readFileSync(
      new URL(`${print}/${gcode}`, TEST_PRINTS),
      'utf8',
    );
    const expected: unknown = JSON.parse(
      readFileSync(
        new URL(`${print}/expected-summary.json`, TEST_PRINTS),
        'utf8',
      ),
    );

    const { summary } = await parseGcodeText([text], { segmentBudget: BUDGET });

    expect(toJson(SliceSummarySchema, summary)).toEqual(expected);
  });
});
