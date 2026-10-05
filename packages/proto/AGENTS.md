# Agent Instructions: `packages/proto/`

The API contract every service and client is generated from. The root `AGENTS.md` still applies
in full; this file adds the rules for shaping the contract. The human-facing overview, with a
diagram, is `README.md` beside this file. Keep the two in step.

## Domain-driven layout

Packages follow the domains in `data-management-choices.md`. There are four kinds:

| Kind | Packages | Holds | May import |
| --- | --- | --- | --- |
| ID kernel | `id.v1` | One strongly typed ID per entity | nothing |
| Shared units | `common.v1` | Base units every package reuses (`TimeStatus`, `PageRequest`/`PageResponse`) and application metadata | `google.protobuf.*` |
| Domain | `user.v1`, `file.v1`, `print_job.v1`, `printer.v1` | One bounded context's entities, value types and enums | `id.v1`, `common.v1`, `google.protobuf.*` |
| Server (API layer) | `server.v1` (remote server), `printer_server.v1` (on-premise printer server) | Services, RPCs and their request/response messages | domains, `id.v1`, `common.v1`, `google.protobuf.*` |

Never put domain types in `common.v1`. It holds only units with no domain meaning.

- **Domains couple by ID only.** A domain package never imports another domain package. A job
  refers to its file as `id.v1.FileId file_id`, never by embedding `file.v1.File`.
- **Composition happens in server packages.** When a response needs data from several domains,
  the server message carries each one side by side, e.g. `GetPrintJobResponse { print_job, file }`.
- **A service lives with the server that serves it**, not with a domain. Name services after the
  domain they expose (`PrintJobService`), not after the server.

### Adding a domain

1. Create `<domain>/v1/<domain>.proto` with `package <domain>.v1;`.
2. Create `id/v1/<domain>_id.proto` holding `<Entity>Id` for each of its entities.
3. Expose it through a service in the server package that owns it.

## Strongly typed IDs

Every identifier crosses the wire as an `id.v1` message, never a bare `string`. Each entity has
its own type, so passing a printer's ID where a job's belongs is a compile error in the generated
TypeScript and a pyright error in Python. That is caught at build time, for every developer and
agent, rather than in review.

- Every `id.v1` message is `<Entity>Id { string value = 1; }`, and the value is a UUID.
- One file per domain in `id/v1/`, named `<domain>_id.proto`, headed by the comment
  "Strongly typed DDD domain ID". Adding an entity adds a file, so concurrent work does not
  collide.
- An entity's own ID field is `id`, typed `id.v1.<Entity>Id`.
- Every other ID field is named exactly after its type: `printer_id` holds `id.v1.PrinterId`.
  No prefixes or suffixes (`assigned_printer_id`, `current_print_job_id` are wrong). Plural
  `printer_ids` for repeated.
- `packages/proto/utils/tests/test_typed_ids.py` enforces all of the above.

## Naming

- Keep names minimal and consistent: `filename`, `user_id`, `user_notes`, `time_status`. Drop
  any word the message already implies (`original_`, `owner_`, `status_`).
- Requests and responses are `<Rpc>Request` / `<Rpc>Response` (buf STANDARD).
- Stay vendor-neutral. No printer-vendor formats or terms in names: `FILE_TYPE_CGCODE` covers
  every compressed GCODE format. Vendor specifics belong in adapters.

## Enums

- `_UNSPECIFIED = 0` and is never valid. Values are prefixed with the enum name.
- **Append only.** Never remove or renumber a value; `buf breaking` rejects it.
- Mark staff-only values in their comment (`PRINT_JOB_STATUS_UNDER_REVIEW`).
- `UserRole` is numbered from least to most access, but never compare roles numerically. Check
  for the roles a permission allows.
- The database stores its own stable IDs for enum values and maps them to these enums in
  persistence code. The wire carries the enum.

## Base units

`common.v1` holds base units, such as `TimeStatus` and `PageRequest`/`PageResponse`. Check it
before building a new proto, and reuse or extend a base unit rather than adding a parallel shape.

## Patterns

**The entity comes first.** Create the domain entity as a draft before anything is attached to
it. Dependents link to an entity that already exists, so every link is visible in the contract.
For print jobs: `CreatePrintJob` → `CreatePrintJobUpload` → PUT → `SubmitPrintJob`.

**Large-file upload pair.** Never put file bytes in an RPC; browsers cannot stream them through
Connect.

1. `Create<Thing>Upload(<thing>_id, file.v1.FileUploadMetadata)` creates the `file.v1.File`,
   links it to the entity, and returns a `file.v1.FileUploadSlot { file_id, upload_url }`
   (call 1 of 2). Calling it again replaces the file.
2. The client HTTP PUTs the raw bytes to `slot.upload_url` (call 2 of 2). The slot expires a
   server-configured time after the file's `time_status.updated_at`.

Reuse the `file.v1` upload types and comment both calls as a pair.

**Status transitions.** Staff-driven changes to one entity go through a single
`Transition<Entity>` RPC with a `oneof action`, one nested message per action carrying exactly
the fields that action needs. Add an action as a new oneof case. Statuses set by printers or
other services are reported by those services, not requested through this RPC.

**Idempotent commands.** A command that causes a physical action carries an `id.v1.CommandId`
chosen by the caller. A retry with the same ID returns the first result.

## Not in the contract yet

- **Authentication and caller identity.** Do not add actor fields or auth headers.
- **Storage keys and file paths.** Files are referenced by `id.v1.FileId` only.

## Checks

| Check | Command |
| --- | --- |
| Lint, including a comment on every element | `buf lint` |
| No breaking change against `main` | `buf breaking --against ".git#branch=main"` |
| Typed-ID and TimeStatus rules | `uv run --project packages/proto/utils pytest packages/proto/utils/tests` |

Every message, field, enum, enum value, oneof, service and RPC needs a one-line `//` comment
saying what it is. The comment explains, it does not restate the name.
