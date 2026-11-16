import { Card, CardHeader, CardTitle, cn } from '@armada/ui-kit';
import { useEffect } from 'react';
import { useOutletContext } from 'react-router';

import { NewPrintDialog } from '../components/NewPrintDialog';
import { routePaths } from '../routes';

// STUB: the frames from the design with their titles only. Each card's content belongs to the
// feature ticket that owns it.
function PlaceholderCard({
  title,
  className,
}: {
  title: string;
  className?: string;
}) {
  return (
    <Card className={cn('border-border', className)}>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
    </Card>
  );
}

export function HomePage() {
  const { dialogOpen, closeDialog } = useOutletContext<{
    dialogOpen: boolean;
    closeDialog: () => void;
  }>();
  useEffect(() => {
    closeDialog();
  }, [closeDialog]);
  return (
    <>
      <div aria-hidden="true">
        <div className="h-[50px] bg-primary" />
        <div className="h-[50px] bg-accent" />
      </div>
      <div className="grid gap-6 p-8 xl:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <h1 className="sr-only">{routePaths.home.label}</h1>
        <div className="grid content-start gap-6">
          <PlaceholderCard title="Welcome back" className="min-h-48" />
          <PlaceholderCard title="Start a new print" className="min-h-64" />
          <PlaceholderCard title="Recent updates" className="min-h-48" />
        </div>
        <NewPrintDialog open={dialogOpen} onClose={closeDialog} />
        <PlaceholderCard title="Your print jobs" className="min-h-96" />
      </div>
    </>
  );
}
