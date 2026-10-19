# `packages/api-client/` — the API client

The web app's typed ConnectRPC client and the generated TypeScript contract from
`packages/proto/`. Generated output lives in `src/gen/`, which is gitignored; run
`python scripts/generate_proto.py buf.gen.web_ts.yaml --node-modules apps/web/node_modules`
from the repository root to refresh it. Never hand-edit generated files.

The RPC transport uses the official [`connect-es`](https://github.com/connectrpc/connect-es)
TypeScript libraries for generated-service dispatch and standard Connect error parsing. Native
`fetch` is used only for the signed file PUT, which is not an RPC.

Create a client with `createApiClient()`. Its `printJobs` API exposes
`createPrintJob`, `createPrintJobUpload`, `uploadPrintJobFile`, `submitPrintJob`,
`listPrintJobs`, and `getPrintJob`. RPC arguments and results come from the generated
`server.v1` messages. Pagination uses the generated `PageRequest` and `PageResponse`.

The file-upload sequence is:

1. Call `createPrintJob` to create a DRAFT job.
2. Call `createPrintJobUpload` with the generated upload metadata.
3. Call `uploadPrintJobFile` with the returned generated slot and a `Blob`/`File`; it PUTs the
   raw bytes to the opaque `uploadUrl`.
4. Call `submitPrintJob` after the upload succeeds.

`uploadUrl` is a short-lived credential. The client does not log it, and upload HTTP failures
throw `PrintJobUploadError` containing only the HTTP status. Fetch/network failures propagate.
RPC failures reject with the ConnectRPC `ConnectError`, preserving its code, metadata and
details. The generated `PrintJobStatus` enum is re-exported; `UNSPECIFIED` is invalid, and
students must see `UNDER_REVIEW` as `SUBMITTED`.

**Belongs here:** client construction, transport configuration, and shared error mapping.

**Does not belong here:** React hooks, component state, routes, or UI policy.
