import { create } from "@bufbuild/protobuf";
import { VersionInfoSchema } from "../gen/common/v1/application_info_pb";

// The web app's own version: package.json's `version`, injected at build time by vite.config.ts.
export function version() {
  const match = /^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$/.exec(__APP_VERSION__);
  if (!match) throw new Error(`package.json version "${__APP_VERSION__}" is not major.minor.maintenance[-postfix]`);
  const [, major, minor, maintenance, postfix] = match;
  return create(VersionInfoSchema, {
    major: Number(major),
    minor: Number(minor),
    maintenance: Number(maintenance),
    postfix,
  });
}