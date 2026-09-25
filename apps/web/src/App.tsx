import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@armada/ui-kit";

const App: React.FC = () => {
  return (
    <main className="min-h-full bg-background p-8 text-foreground">
      <div className="mx-auto max-w-2xl">
        <h1 className="mb-6 text-3xl font-bold">Shared component library</h1>
        <Card>
          <CardHeader>
            <CardTitle>Printer fleet</CardTitle>
            <CardDescription>This card is rendered by the shared UI kit.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm">The web application consumes the same component as the desktop application.</p>
          </CardContent>
        </Card>
      </div>
    </main>
  );
};

export default App;
