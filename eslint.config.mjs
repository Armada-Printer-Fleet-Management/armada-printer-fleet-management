// Shared lint rules for the web app, desktop frontend, and TypeScript packages.
import js from '@eslint/js';
import { plugin as shadcn } from '@shadcn/lint';
import jsxA11y from 'eslint-plugin-jsx-a11y';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import tseslint from 'typescript-eslint';

const typescriptFiles = ['apps/**/*.{ts,tsx}', 'packages/**/*.{ts,tsx}'];

export default tseslint.config(
  {
    ignores: [
      '**/node_modules/**',
      '**/.pnpm-store/**',
      '**/gen/**',
      '**/*_gen/**',
      '**/dist/**',
      '**/build/**',
      '**/coverage/**',
      '**/.idea/**',
      '**/.vscode/**',
      '**/.env',
      '**/.env.*',
    ],
  },
  {
    files: typescriptFiles,
    extends: [
      js.configs.recommended,
      ...tseslint.configs.recommendedTypeChecked,
    ],
    languageOptions: {
      parserOptions: {
        projectService: true,
      },
    },
    plugins: { shadcn },
  },
  {
    files: [
      'apps/web/**/*.{ts,tsx}',
      'apps/desktop/frontend/**/*.{ts,tsx}',
      'packages/ui-kit/**/*.{ts,tsx}',
      'packages/slicer/**/*.{ts,tsx}',
    ],
    languageOptions: {
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
    },
    plugins: {
      react,
      'react-hooks': reactHooks,
      'jsx-a11y': jsxA11y,
    },
    settings: {
      react: { version: 'detect' },
    },
    rules: {
      ...react.configs.recommended.rules,
      ...react.configs['jsx-runtime'].rules,
      ...reactHooks.configs.recommended.rules,
      ...jsxA11y.flatConfigs.recommended.rules,
      // A scrollable <pre> must take focus so a keyboard can scroll it (axe: scrollable-region-focusable).
      'jsx-a11y/no-noninteractive-tabindex': [
        'error',
        { tags: ['pre'], roles: ['tabpanel'], allowExpressionValues: true },
      ],
      'react/prop-types': 'off',
    },
  },
);
