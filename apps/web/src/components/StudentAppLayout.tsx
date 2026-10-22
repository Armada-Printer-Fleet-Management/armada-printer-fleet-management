import { Outlet } from 'react-router';

import { StudentNavBar } from './StudentNavBar';

export function StudentAppLayout() {
  return (
    <div className="min-h-full bg-background text-foreground">
      <header className="border-b border-border px-8 py-4">
        <div className="mx-auto max-w-5xl">
          <StudentNavBar />
        </div>
      </header>
      <Outlet />
    </div>
  );
}
