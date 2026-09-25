import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
import { defineConfig, searchForWorkspaceRoot } from "vite";
import { read } from "../../../packages/organization-info/organization-info";
import { OrganizationInfoSchema } from "./src/gen/common/v1/organization_info_pb";

const organizationInfoDir = fileURLToPath(
  new URL("../../../packages/organization-info", import.meta.url),
);
const uiKitDir = fileURLToPath(new URL("../../../packages/ui-kit", import.meta.url));
const { title } = read(OrganizationInfoSchema);

export default defineConfig({
  plugins: [
    react(),
    {
      name: "organization-title",
      transformIndexHtml: {
        order: "pre",
        handler: (html) => html.replaceAll("%ORGANIZATION_TITLE%", title),
      },
    },
  ],
  // file:// loading (the default run mode) needs relative asset URLs, not root-absolute ones.
  base: "./",
  resolve: {
    alias: { "@organization-info": organizationInfoDir, "@ui-kit": uiKitDir },
    // packages/ sits outside this project, so its files would not find this project's installs.
    dedupe: ["@bufbuild/protobuf", "react", "react-dom"],
  },
  server: {
    port: 5173,
    strictPort: true,
    fs: { allow: [searchForWorkspaceRoot(process.cwd()), organizationInfoDir, uiKitDir] },
  },
});