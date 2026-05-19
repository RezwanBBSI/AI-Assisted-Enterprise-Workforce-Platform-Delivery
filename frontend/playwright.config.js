// @ts-check
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30_000,
  retries: 0,
  use: {
    baseURL: 'http://localhost:8000',
    extraHTTPHeaders: {
      'Content-Type': 'application/json',
    },
  },
  // No browser UI needed for API-level E2E tests
  projects: [
    {
      name: 'api-e2e',
      use: {},
    },
  ],
});
