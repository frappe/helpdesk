// Helpers for the security checks: act from inside the running app as a
// signed-in user, and record every decision as evidence.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const EVIDENCE = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../security/evidence");

/** Open the app shell for `role` so the page holds that user's session and CSRF token. */
export async function openApp(app, role) {
  const page = await app.pageAs(role);
  if (role) {
    await page.goto(role === "agent" ? "/helpdesk/tickets" : "/helpdesk/my-tickets");
    await page.waitForFunction(() => typeof window.csrf_token === "string" && window.csrf_token.length > 10);
  }
  return page;
}

/**
 * Send a request the way the app's own code does: same origin, the session
 * cookie, and (unless `csrf` is false) the CSRF token header.
 */
export async function inApp(page, method, url, body, { csrf = true } = {}) {
  return page.evaluate(
    async ({ method, url, body, csrf }) => {
      const headers = { Accept: "application/json" };
      if (body !== undefined) headers["Content-Type"] = "application/json";
      if (csrf && window.csrf_token) headers["X-Frappe-CSRF-Token"] = window.csrf_token;
      const response = await fetch(url, {
        method,
        headers,
        body: body === undefined ? undefined : JSON.stringify(body),
        credentials: "same-origin",
      });
      const text = await response.text();
      let json = null;
      try {
        json = JSON.parse(text);
      } catch {
        // not JSON
      }
      return { status: response.status, json, text: text.slice(0, 600) };
    },
    { method, url, body, csrf }
  );
}

/** Short server explanation of a refusal, for the evidence column. */
export function reason(result) {
  const json = result.json || {};
  let messages = "";
  try {
    messages = JSON.parse(json._server_messages || "[]")
      .map((m) => JSON.parse(m).message)
      .join(" / ");
  } catch {
    messages = "";
  }
  return (json.exc_type ? `${json.exc_type}: ` : "") + (messages || json._error_message || json.exception || "").toString().replace(/<[^>]+>/g, "").slice(0, 160);
}

/** Collects check records and writes them when the file's tests finish. */
export class Evidence {
  constructor(name) {
    this.name = name;
    this.rows = [];
  }

  add(row) {
    this.rows.push({ ...row, at: new Date().toISOString() });
  }

  write() {
    fs.mkdirSync(EVIDENCE, { recursive: true });
    fs.writeFileSync(path.join(EVIDENCE, `${this.name}.json`), JSON.stringify(this.rows, null, 2) + "\n");
    const header = Object.keys(this.rows[0] || {}).filter((k) => k !== "at");
    const lines = [
      `| ${header.join(" | ")} |`,
      `|${header.map(() => "---").join("|")}|`,
      ...this.rows.map((r) => `| ${header.map((k) => String(r[k] ?? "").replace(/\|/g, "\\|").replace(/\n/g, " ")).join(" | ")} |`),
    ];
    fs.writeFileSync(path.join(EVIDENCE, `${this.name}.md`), lines.join("\n") + "\n");
  }

  screenshotPath(id) {
    fs.mkdirSync(path.join(EVIDENCE, "screens"), { recursive: true });
    return path.join(EVIDENCE, "screens", `${id}.png`);
  }
}
