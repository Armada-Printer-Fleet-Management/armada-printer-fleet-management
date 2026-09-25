// TODO TEMP DOCUMENT, PLEASE REPLACE BUT KEEP VERSION API CALL EXAMPLE
// THAT IS INSIDE AN ABOUT PAGE

import { read } from "@organization-info/organization-info";
import { AboutBox } from "@ui-kit/about-box";
import { useEffect, useState } from "react";
import { OrganizationInfoSchema } from "./gen/common/v1/organization_info_pb";
import { version } from "./ipc/application-info";

type VersionState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; version: Awaited<ReturnType<typeof version>> };

export function App() {
  const [state, setState] = useState<VersionState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    version()
      .then((info) => {
        if (cancelled) return;
        setState({ status: "ready", version: info });
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
      <AboutBox
        organization={read(OrganizationInfoSchema)}
        version={state.status === "ready" ? state.version : undefined}
      />
      {state.status === "loading" && <p>Loading backend version…</p>}
      {state.status === "error" && <p>Failed to reach the backend: {state.message}</p>}
    </main>
  );
}
