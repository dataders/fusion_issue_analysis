const { defineConfig, devices } = require("@playwright/test");
const fs = require("fs");

// Load .env.local for local development
if (fs.existsSync(".env.local")) {
  fs.readFileSync(".env.local", "utf8")
    .split("\n")
    .forEach((line) => {
      const eq = line.indexOf("=");
      if (eq > 0) {
        const k = line.slice(0, eq).trim();
        const v = line.slice(eq + 1).trim();
        if (k && !(k in process.env)) process.env[k] = v;
      }
    });
}

const port = process.env.PLAYWRIGHT_PORT || 9321;
const baseURL = `http://127.0.0.1:${port}`;

module.exports = defineConfig({
  testDir: "tests/ui",
  timeout: 45_000,
  expect: {
    timeout: 7_500,
  },
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI
    ? [["list"], ["html", { open: "never" }]]
    : [["list"]],
  use: {
    baseURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: {
    // Use the COEP server so DuckDB-WASM live tabs work in tests
    command: `uv run python3 dashboard/serve_local.py`,
    url: `${baseURL}/index.html`,
    reuseExistingServer: !process.env.CI,
    timeout: 15_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
