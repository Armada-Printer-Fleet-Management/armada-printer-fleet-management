import { Outlet } from 'react-router';

import { Sidebar } from './Sidebar';

export function AppLayout() {
  return (
    <div className="flex h-screen bg-background text-foreground">
      <Sidebar />
      <main className="relative min-w-0 flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
