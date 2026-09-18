// Runs a *.check.ts script through Vite so it can import modules that pull in
// frappe-ui (its index loads .vue files, which plain tsx cannot). Usage:
//   node run-check.mjs src/composables/useSLA.check.ts
import { createServer } from "vite";

const server = await createServer({
  configFile: "vite.config.js",
  // not "development": that mode spawns the doctype type generator, which
  // needs a running site and rewrites src/types/doctypes.ts
  mode: "check",
  server: { middlewareMode: true },
  // dayjs/esm uses extensionless imports, so Node cannot load it externalized
  ssr: { noExternal: ["dayjs"] },
  logLevel: "error",
});

try {
  await server.ssrLoadModule("/" + process.argv[2]);
} finally {
  await server.close();
}
