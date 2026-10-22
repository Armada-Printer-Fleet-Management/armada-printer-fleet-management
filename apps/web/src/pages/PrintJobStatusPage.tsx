import { TempRoutePage } from '@armada/ui-kit';
import { useParams } from 'react-router';

// TEMPORARY: this route placeholder verifies dynamic navigation. Replace it
// with the print-job status page when that feature is implemented.
export function PrintJobStatusPage() {
  const { printJobId } = useParams();

  return (
    <main className="min-h-full bg-background p-8 text-foreground">
      <div className="mx-auto max-w-2xl">
        <TempRoutePage
          heading="Print job status"
          description={
            printJobId
              ? `Status page for print job ${printJobId}.`
              : 'No print job ID was provided.'
          }
        />
      </div>
    </main>
  );
}
