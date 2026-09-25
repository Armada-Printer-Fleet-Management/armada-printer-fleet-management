import { type DescMessage, type MessageShape, fromJson } from "@bufbuild/protobuf";
import organizationJson from "./organization.json";

// The caller passes its own generated OrganizationInfoSchema, so this file never depends on one app's gen tree.
export function read<Desc extends DescMessage>(schema: Desc): MessageShape<Desc> {
  return fromJson(schema, organizationJson);
}
