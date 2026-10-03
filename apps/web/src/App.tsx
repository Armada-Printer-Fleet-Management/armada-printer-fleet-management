import { read } from "@armada/organization-info";
import React from "react";
import { AboutBox, Card, CardContent, CardDescription, CardHeader, CardTitle } from "@armada/ui-kit";
import { OrganizationInfoSchema } from "./gen/common/v1/organization_info_pb";
import { version } from "./lib/version";

const App: React.FC = () => {
  return (
  <div className="app">
      <header>
          <AboutBox organization={read(OrganizationInfoSchema)} version={version()} />
      </header>
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
  </div>
  );
};

export default App;