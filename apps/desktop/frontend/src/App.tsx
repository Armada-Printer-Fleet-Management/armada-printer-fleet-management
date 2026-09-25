// TODO TEMP DOCUMENT, PLEASE REPLACE BUT KEEP VERSION API CALL EXAMPLE
// THAT IS INSIDE AN ABOUT PAGE

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@armada/ui-kit";
import { version } from "./ipc/application-information";

type VersionState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; text: string };

export function App() {
  const [state, setState] = useState<VersionState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    version()
      .then((info) => {
        if (cancelled) return;
        const text = `${info.major}.${info.minor}.${info.maintenance}${info.postfix ? `-${info.postfix}` : ""}`;
        setState({ status: "ready", text });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setState({ status: "error", message: error instanceof Error ? error.message : String(error) });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="min-h-full bg-background p-8 text-foreground">
      <h1 className="mb-6 text-3xl font-bold">About</h1>
      <Card className="max-w-xl">
        <CardHeader>
          <CardTitle>Printer fleet</CardTitle>
          <CardDescription>This card is rendered by the shared UI kit.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm">The desktop application consumes the same component as the web application.</p>
        </CardContent>
      </Card>
      {state.status === "loading" && <p>Loading backend version…</p>}
      {state.status === "error" && <p>Failed to reach the backend: {state.message}</p>}
      {state.status === "ready" && <p>Backend version: {state.text}</p>}
    </main>
  );
}