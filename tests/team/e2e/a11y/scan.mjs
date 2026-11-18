// Accessibility scans of the key screens: a full axe-core scan through
// @axe-core/playwright and a Lighthouse run (accessibility, best practices,
// SEO), both on the logged-in screen.
//
//   node a11y/scan.mjs <phase>        phase = before | after (folder name)
//
// Lighthouse is run against the same Chromium that Playwright drives, through
// its remote-debugging port, so it reuses the logged-in session (the
// "login script" route of the brief). Reports go to
// tests/team/a11y/evidence/<phase>/ and a summary to summary.json / summary.md.
import AxeBuilder from "@axe-core/playwright";
import { chromium, expect } from "@playwright/test";
import lighthouse from "lighthouse";
import desktopConfig from "lighthouse/core/config/desktop-config.js";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const TEAM = path.resolve(HERE, "../..");
const SEED = path.join(TEAM, "seed.sh");
const BASE = process.env.SQE_BASE_URL || "http://127.0.0.1:8000";
const PHASE = process.argv[2] || "before";
const OUT = path.join(TEAM, "a11y", "evidence", PHASE);
const ENV = Object.fromEntries(
  fs.readFileSync(path.join(TEAM, ".env"), "utf8").split("\n")
    .filter((l) => l.includes("=") && !l.startsWith("#"))
    .map((l) => [l.slice(0, l.indexOf("=")), l.slice(l.indexOf("=") + 1).trim()])
);
const ACCOUNTS = { customer: "SQE_CUSTOMER_A", agent: "SQE_AGENT" };
const PORT = 9333;

// --- arrange: one resolved ticket with an agent reply ------------------------
async function arrange() {
  execFileSync("bash", [SEED, "reset"], { stdio: "pipe" });
  const browser = await chromium.launch();
  const login = async (role) => {
    const ctx = await browser.newContext();
    const r = await ctx.request.post(`${BASE}/api/method/login`, {
      data: { usr: ENV[`${ACCOUNTS[role]}_EMAIL`], pwd: ENV[`${ACCOUNTS[role]}_PASSWORD`] },
    });
    if (r.status() !== 200) throw new Error(`login failed for ${role}`);
    return ctx.request;
  };
  const customer = await login("customer");
  const agent = await login("agent");
  const create = async (subject) => {
    const r = await customer.post(`${BASE}/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.new`, {
      data: { doc: { subject, description: "<p>The printer on floor 2 jams on every page.</p>" } },
    });
    return (await r.json()).message.name;
  };
  const resolved = await create("Printer on floor 2 jams");
  execFileSync("bash", [SEED, "agent-reply", "--ticket", String(resolved)], { stdio: "pipe" });
  await agent.put(`${BASE}/api/resource/HD Ticket/${resolved}`, { data: { status: "Resolved" } });
  const open = await create("Monitor flickers after update");
  await browser.close();
  return { resolved, open };
}

// --- the screens -------------------------------------------------------------
function screens({ resolved, open }) {
  return [
    {
      id: "s1_new_ticket", role: "customer", useCase: "UC-01",
      title: "Customer: New Ticket form", url: "/helpdesk/my-tickets/new",
      // the description editor and Submit only appear once a subject is typed
      prepare: async (page) => {
        await page.getByRole("textbox", { name: "A short description" }).fill("Printer jams");
      },
    },
    {
      id: "s2_customer_ticket", role: "customer", useCase: "UC-02, UC-05",
      title: "Customer: ticket page (resolved)", url: `/helpdesk/my-tickets/${resolved}`,
    },
    {
      id: "s3_rating_dialog", role: "customer", useCase: "UC-02", axeOnly: true,
      title: "Customer: Rate this ticket dialog", url: `/helpdesk/my-tickets/${resolved}`,
      prepare: async (page) => {
        // the button reacts only once the ticket has loaded, so retry until the dialog opens
        const dialog = page.getByRole("dialog", { name: "Rate this ticket" });
        await expect(async () => {
          await page.getByRole("button", { name: "Close", exact: true }).click();
          await expect(dialog).toBeVisible({ timeout: 3000 });
        }).toPass({ timeout: 30_000 });
        await page.getByRole("radio", { name: "4 of 5" }).click();
      },
    },
    {
      id: "s4_customer_list", role: "customer", useCase: "UC-06",
      title: "Customer: ticket list", url: "/helpdesk/my-tickets",
    },
    {
      id: "s5_agent_ticket", role: "agent", useCase: "UC-03, UC-04",
      title: "Agent: ticket page", url: `/helpdesk/tickets/${open}`,
    },
  ];
}

// --- scanning ------------------------------------------------------------------
async function withLoggedInBrowser(role, fn) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "sqe-a11y-"));
  const context = await chromium.launchPersistentContext(dir, {
    args: [`--remote-debugging-port=${PORT}`],
    viewport: { width: 1350, height: 940 },
  });
  try {
    const r = await context.request.post(`${BASE}/api/method/login`, {
      data: { usr: ENV[`${ACCOUNTS[role]}_EMAIL`], pwd: ENV[`${ACCOUNTS[role]}_PASSWORD`] },
    });
    if (r.status() !== 200) throw new Error(`login failed for ${role}`);
    return await fn(context);
  } finally {
    await context.close();
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

async function settle(page) {
  await page.waitForLoadState("networkidle").catch(() => {});
  await page.waitForTimeout(1000);
}

async function runAxe(context, screen) {
  const page = await context.newPage();
  await page.goto(BASE + screen.url);
  await settle(page);
  if (screen.prepare) await screen.prepare(page);
  await settle(page);
  // Full scan: every rule axe-core ships, not a subset of tags. Legacy mode:
  // the default frame handling never returns on the agent page's message
  // iframe (about:srcdoc); legacy mode still scans inside it. Used for every
  // screen so the results are comparable.
  const result = await new AxeBuilder({ page }).setLegacyMode(true).analyze();
  await page.close();
  fs.writeFileSync(path.join(OUT, `${screen.id}.axe.json`), JSON.stringify(result, null, 2));
  return result.violations.map((v) => ({
    tool: "axe",
    id: v.id,
    impact: v.impact,
    help: v.help,
    wcag: v.tags.filter((t) => /^wcag\d/.test(t)).join(" "),
    elements: v.nodes.map((n) => n.target.join(" ")),
  }));
}

async function runLighthouse(screen) {
  const result = await lighthouse(
    BASE + screen.url,
    {
      port: PORT,
      output: ["html", "json"],
      logLevel: "error",
      onlyCategories: ["accessibility", "best-practices", "seo"],
      disableStorageReset: true, // keep the logged-in session
    },
    desktopConfig
  );
  const [html, json] = result.report;
  fs.writeFileSync(path.join(OUT, `${screen.id}.lighthouse.html`), html);
  fs.writeFileSync(path.join(OUT, `${screen.id}.lighthouse.json`), json);
  const lhr = result.lhr;
  const scores = Object.fromEntries(
    Object.entries(lhr.categories).map(([key, c]) => [key, Math.round(c.score * 100)])
  );
  const failed = [];
  for (const [category, c] of Object.entries(lhr.categories)) {
    for (const ref of c.auditRefs) {
      const audit = lhr.audits[ref.id];
      if (audit.scoreDisplayMode === "notApplicable" || audit.scoreDisplayMode === "manual") continue;
      if (audit.scoreDisplayMode === "informative") continue;
      if (audit.score === null || audit.score >= 1) continue;
      const items = audit.details?.items || [];
      failed.push({
        tool: "lighthouse",
        category,
        id: ref.id,
        title: audit.title,
        weight: ref.weight,
        elements: items
          .map((i) => i.node?.selector || i.source?.url || i.url || i.description || "")
          .filter(Boolean)
          .slice(0, 12),
      });
    }
  }
  return { scores, finalUrl: lhr.finalDisplayedUrl, failed };
}

// --- main ------------------------------------------------------------------------
fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT, { recursive: true });
const data = await arrange();
const summary = { phase: PHASE, date: new Date().toISOString(), base: BASE, screens: [] };

for (const screen of screens(data)) {
  const entry = { id: screen.id, title: screen.title, useCase: screen.useCase, url: screen.url };
  await withLoggedInBrowser(screen.role, async (context) => {
    entry.axe = await runAxe(context, screen);
    if (!screen.axeOnly) entry.lighthouse = await runLighthouse(screen);
  });
  summary.screens.push(entry);
  console.log(
    `${screen.id}: axe ${entry.axe.length} rule(s) violated` +
      (entry.lighthouse ? ` | lighthouse ${JSON.stringify(entry.lighthouse.scores)} (${entry.lighthouse.failed.length} failed audits)` : "")
  );
}

fs.writeFileSync(path.join(OUT, "summary.json"), JSON.stringify(summary, null, 2));

// a readable summary
const lines = [`# Accessibility scan: ${PHASE}`, "", `Run ${summary.date} against ${BASE}.`, ""];
lines.push("| Screen | Use case | Lighthouse a11y | Best practices | SEO | axe rules violated | axe elements |");
lines.push("|---|---|---|---|---|---|---|");
for (const s of summary.screens) {
  const sc = s.lighthouse?.scores || {};
  const nodes = s.axe.reduce((n, v) => n + v.elements.length, 0);
  lines.push(`| ${s.title} | ${s.useCase} | ${sc.accessibility ?? "-"} | ${sc["best-practices"] ?? "-"} | ${sc.seo ?? "-"} | ${s.axe.length} | ${nodes} |`);
}
for (const s of summary.screens) {
  lines.push("", `## ${s.title}`, "", "| Tool | Rule / audit | Impact / category | Elements |", "|---|---|---|---|");
  for (const v of s.axe) lines.push(`| axe | ${v.id}: ${v.help} | ${v.impact} | ${v.elements.slice(0, 4).join("<br>")}${v.elements.length > 4 ? ` (+${v.elements.length - 4})` : ""} |`);
  for (const a of s.lighthouse?.failed || []) lines.push(`| lighthouse | ${a.id}: ${a.title} | ${a.category} | ${a.elements.slice(0, 4).join("<br>")} |`);
}
fs.writeFileSync(path.join(OUT, "summary.md"), lines.join("\n") + "\n");
execFileSync("bash", [SEED, "reset"], { stdio: "pipe" });
console.log(`written: ${OUT}`);
