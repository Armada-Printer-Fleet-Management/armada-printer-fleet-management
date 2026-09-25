# `packages/organization-info/` — identity shared by every application

`organization.json` holds the generic reusable organization information (title, description,
license, source repository), typed by the `OrganizationInfo` message in
`packages/proto/common/v1/organization_info.proto`.
Use this one file rather than each hardcoding it, so it changes in one place.