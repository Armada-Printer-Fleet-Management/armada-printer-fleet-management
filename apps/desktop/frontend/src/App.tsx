// TODO TEMP DOCUMENT, PLEASE REPLACE BUT KEEP VERSION API CALL EXAMPLE
// THAT IS INSIDE AN ABOUT PAGE

import { useEffect, useState } from "react";
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
    <main>
      <h1>About</h1>
      <h3>Armada - Printer Fleet Management</h3>
      {state.status === "loading" && <p>Loading backend version…</p>}
      {state.status === "error" && <p>Failed to reach the backend: {state.message}</p>}
      {state.status === "ready" && <p>Backend version: {state.text}</p>}
    </main>
  );
}