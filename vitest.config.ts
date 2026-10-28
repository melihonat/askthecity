import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: { alias: { "@": new URL(".", import.meta.url).pathname.replace(/^\/(\w:)/, "$1") } },
  test: { include: ["lib/**/*.test.ts"] },
});
