// Team browser tests. Run from tests/team/e2e:  npx playwright test
import { defineConfig, devices } from "@playwright/test";

// SQE_PROXY=http://127.0.0.1:8090 sends all browser traffic through a proxy
// (OWASP ZAP in passive mode, see ../security/zap_passive.sh). Chromium skips
// proxies for loopback addresses unless told not to.
const proxy = process.env.SQE_PROXY
  ? {
      proxy: { server: process.env.SQE_PROXY, bypass: "" },
      launchOptions: { args: ["--proxy-bypass-list=<-loopback>"] },
      ignoreHTTPSErrors: true,
    }
  : {};

export default defineConfig({
  testDir: ".",
  testMatch: ["usecases/**/*.spec.mjs", "usability/**/*.spec.mjs", "security/**/*.spec.mjs"],
  globalSetup: "./support/global-setup.mjs",
  // the flows share one site and its seeded accounts, so they run one at a time
  workers: 1,
  fullyParallel: false,
  retries: 0,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: [
    ["list"],
    ["html", { outputFolder: "../reports/e2e/html", open: "never" }],
    ["junit", { outputFile: "../reports/e2e/junit.xml" }],
  ],
  outputDir: "../reports/e2e/artifacts",
  use: {
    baseURL: process.env.SQE_BASE_URL || "http://127.0.0.1:8000",
    ...devices["Desktop Chrome"],
    viewport: { width: 1366, height: 900 },
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    ...proxy,
  },
});
