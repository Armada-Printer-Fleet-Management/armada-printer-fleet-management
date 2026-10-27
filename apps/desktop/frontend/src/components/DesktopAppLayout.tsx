import { Outlet } from 'react-router';

import { DesktopNavRail } from './DesktopNavRail';

export function DesktopAppLayout() {
  return (
    <div className="flex h-screen bg-background text-foreground">
      <DesktopNavRail />
      <main className="relative min-w-0 flex-1 overflow-y-auto p-8">
        <Outlet />
      </main>
    </div>
  );
}
