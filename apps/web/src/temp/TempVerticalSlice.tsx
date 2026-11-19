// TEMPORARY: the web app's entries on the shared vertical slice page. Delete this folder with
// packages/ui-kit/src/temp/.

import * as React from 'react';
import { toJson } from '@bufbuild/protobuf';
import { TempVerticalSlicePage, type TempSliceSection } from '@armada/ui-kit';
import type { createApiClient, PrinterType } from '@armada/api-client';
import { bundledPrint, samplePrintUrl } from '@armada/sample-prints';
import { tempSlicerActions, type TempPrinterType } from '@armada/slicer/temp';
import { loadSlicerEngine, slicerEngineUrl } from '@armada/slicer-engine';
import {
  GetPrintJobResponseSchema,
  ListPrintJobsResponseSchema,
} from '@armada/api-client/gen/server/v1/print_job_service_pb';

type ApiClient = ReturnType<typeof createApiClient>;

export function TempVerticalSlice({
  printJobs,
  printers,
  slicerConfiguration,
}: Pick<ApiClient, 'printJobs' | 'printers' | 'slicerConfiguration'>) {
  const [printerTypes, setPrinterTypes] = React.useState<PrinterType[]>([]);

  React.useEffect(() => {
    printers
      .listPrinterTypes()
      .then((response) => setPrinterTypes(response.printerTypes))
      .catch(console.error);
  }, [printers]);

  const sections: TempSliceSection[] = [
    {
      title: 'Print jobs',
      boundary: ['Web UI', 'ConnectRPC', 'Server'],
      actions: [
        {
          label: 'ListPrintJobs',
          run: async () =>
            toJson(
              ListPrintJobsResponseSchema,
              await printJobs.listPrintJobs({ page: { pageSize: 20 } }),
            ),
        },
        {
          label: 'GetPrintJob',
          run: async () => {
            const page = await printJobs.listPrintJobs({
              page: { pageSize: 1 },
            });
            const firstJob = page.printJobs[0];
            if (!firstJob) {
              throw new Error('No print jobs are available to retrieve.');
            }
            return toJson(
              GetPrintJobResponseSchema,
              await printJobs.getPrintJob({ printJobId: firstJob.id }),
            );
          },
        },
      ],
    },
    {
      title: 'Slicer engine',
      boundary: ['Web UI', 'Slicer engine (WASM)'],
      actions: [
        {
          label: 'version',
          run: async () => ({
            version: (
              await loadSlicerEngine(slicerEngineUrl(import.meta.env.BASE_URL))
            ).version(),
          }),
        },
      ],
    },
    {
      title: 'Slicer',
      boundary: [
        'Web UI',
        'ConnectRPC',
        'Server (settings)',
        'Worker',
        'Slicer engine (WASM)',
      ],
      actions: tempSlicerActions({
        engineBase: import.meta.env.BASE_URL,
        printerTypes: printerTypes.map(tempPrinterType),
        sliceSettings: async ({ model }) => {
          const printerType = printerTypes.find((type) => type.model === model);
          const { sliceSettings } = await slicerConfiguration.getSliceSettings({
            printerType,
          });
          if (!sliceSettings) throw new Error('The server sent no settings.');
          return sliceSettings;
        },
        armada: bundledPrint('benchy-armada'),
        fileUrl: (print, file) =>
          samplePrintUrl(import.meta.env.BASE_URL, print, file),
      }),
    },
  ];

  return (
    <TempVerticalSlicePage
      className="mt-8"
      heading="Vertical slice — web"
      sections={sections}
    />
  );
}

function tempPrinterType(type: PrinterType): TempPrinterType {
  return {
    model: type.model,
    bedWidthMm: type.capabilities?.buildVolumeXMm ?? 0,
    bedDepthMm: type.capabilities?.buildVolumeYMm ?? 0,
  };
}
