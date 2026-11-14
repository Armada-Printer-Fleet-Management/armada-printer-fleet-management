import { useCallback, useState } from 'react';
import { Outlet } from 'react-router';

import { NewPrintDialog } from './NewPrintDialog';
import { Sidebar } from './Sidebar';

export function AppLayout() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const closeDialog = useCallback(() => setDialogOpen(false), []);

  return (
    <div className="flex h-screen bg-background text-foreground">
      <Sidebar onNewPrint={() => setDialogOpen(true)} />
      <main className="relative min-w-0 flex-1 overflow-y-auto">
        <Outlet />
      </main>
      <NewPrintDialog open={dialogOpen} onClose={closeDialog} />
    </div>
  );
}
