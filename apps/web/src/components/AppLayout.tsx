import { useCallback, useState } from 'react';
import { Outlet, useLocation } from 'react-router';

import { routePaths } from '../routes';
import { Sidebar } from './Sidebar';

export function AppLayout() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const location = useLocation();
  const closeDialog = useCallback(() => setDialogOpen(false), []);

  return (
    <div className="flex h-screen bg-background text-foreground">
      <Sidebar
        onNewPrint={
          location.pathname === routePaths.home.path
            ? () => setDialogOpen(true)
            : undefined
        }
      />
      <main className="relative min-w-0 flex-1 overflow-y-auto">
        <Outlet context={{ dialogOpen, closeDialog }} />
      </main>
    </div>
  );
}
