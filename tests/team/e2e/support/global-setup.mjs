// Every browser run starts from the seeded state.
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

export const SEED = fileURLToPath(new URL("../../seed.sh", import.meta.url));

export default function globalSetup() {
  execFileSync("bash", [SEED, "reset"], { stdio: "pipe" });
}
