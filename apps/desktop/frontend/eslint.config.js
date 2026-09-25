import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  {
    ignores: [
      "**/node_modules/**",
      "**/gen/**",
      "**/*_gen/**",
      "**/dist/**",
      "**/build/**",
      "**/coverage/**",
      "**/.idea/**",
      "**/.vscode/**",
      "**/.env",
      "**/.env.*",
      "../../../packages/organization-info/**",
    ],
  },
  js.configs.recommended,
  {
    files: ["src/**/*.{ts,tsx}"],
    extends: [...tseslint.configs.recommendedTypeChecked],
    languageOptions: {
      parserOptions: {
        project: "./tsconfig.json",
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
);