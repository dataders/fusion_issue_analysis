const { defineConfig, devices } = require("@playwright/test");

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
    command: `uv run python3 -m http.server ${port} --bind 127.0.0.1 --directory dashboard`,
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
