import { TempRoutePage } from '@armada/ui-kit';

// TEMPORARY: this route placeholder verifies navigation. Replace it with the
// submission form when the print-submission page is implemented.
export function PrintSubmissionPage() {
  return (
    <main className="min-h-full bg-background p-8 text-foreground">
      <div className="mx-auto max-w-2xl">
        <TempRoutePage
          heading="Submit a print"
          description="The print submission form is not implemented yet."
        />
      </div>
    </main>
  );
}
