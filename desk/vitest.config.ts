import path from "path";
import { defineConfig } from "vitest/config";

// Pure TypeScript modules only: nothing here may import frappe-ui or @framework/ui.
export default defineConfig({
  resolve: {
    alias: [
      {
        find: "@/translation",
        replacement: path.resolve(__dirname, "src/test/translation.ts"),
      },
      { find: "@", replacement: path.resolve(__dirname, "src") },
    ],
  },
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
});
