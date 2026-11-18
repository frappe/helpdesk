// Access matrix for the two workflows, verified through the running app.
// Each check acts as one role, records role / action / expected / observed /
// evidence, and asserts the expected decision. A check whose expected
// decision the baseline does not meet is marked as an expected failure and
// recorded as a finding. Matrix and findings: ../../security/SECURITY_REPORT.md
import { emailOf, expect, test } from "../support/app.mjs";
import { Evidence, inApp, openApp, reason } from "../support/security.mjs";

const NEW = "/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.new";
const ONE = "/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.get_one";
const RESOURCE = (name) => `/api/resource/HD Ticket/${name}`;
const evidence = new Evidence("access_matrix");

test.describe.configure({ mode: "serial" });
test.afterAll(() => evidence.write());

/** Run one API-level access decision and record it. */
async function decide(app, { id, role, action, route, expected, request, verify }) {
  const page = await openApp(app, role);
  const result = await request(page);
  const observed = result.status === 200 ? "allowed" : "denied";
  const stored = verify ? await verify() : "";
  evidence.add({
    id,
    role: role || "anonymous",
    action,
    route,
    expected,
    observed,
    evidence: `HTTP ${result.status}${observed === "denied" ? ` ${reason(result)}` : ""}${stored ? `; ${stored}` : ""}`,
  });
  return { observed, result };
}

// --- Customer ------------------------------------------------------------------

test("AC-01 customer may raise a ticket", async ({ app }) => {
  const { observed, result } = await decide(app, {
    id: "AC-01", role: "customerA", action: "raise a ticket", route: `POST ${NEW}`, expected: "allowed",
    request: (page) => inApp(page, "POST", NEW, { doc: { subject: app.subject("AC-01"), description: "<p>x</p>" } }),
  });
  expect(observed).toBe("allowed");
  expect((await app.stored(result.json.message.name)).raised_by).toBe(emailOf("customerA"));
});

test("AC-02 customer may read their own ticket", async ({ app }) => {
  const name = await app.newTicket(app.subject("AC-02"));
  const { observed } = await decide(app, {
    id: "AC-02", role: "customerA", action: "read own ticket", route: `GET ${ONE}`, expected: "allowed",
    request: (page) => inApp(page, "GET", `${ONE}?name=${name}`),
  });
  expect(observed).toBe("allowed");
});

test("AC-03 customer may not read another customer's ticket (screen and API)", async ({ app }) => {
  const name = await app.newTicket(app.subject("AC-03"));
  const page = await openApp(app, "customerB");
  await page.goto(`/helpdesk/my-tickets/${name}`);
  await expect(page.getByText("Not allowed via controller permission check").first()).toBeVisible();
  await expect(page).toHaveURL(/\/helpdesk\/my-tickets$/);
  const shot = evidence.screenshotPath("AC-03_customer_b_other_ticket");
  await page.screenshot({ path: shot });
  const result = await inApp(page, "GET", `${ONE}?name=${name}`);
  evidence.add({
    id: "AC-03", role: "customerB", action: "read another customer's ticket", route: `GET /helpdesk/my-tickets/${name}; GET ${ONE}`,
    expected: "denied", observed: result.status === 200 ? "allowed" : "denied",
    evidence: `screen: "Not allowed via controller permission check", sent back to own list (screens/AC-03_customer_b_other_ticket.png); HTTP ${result.status} ${reason(result)}`,
  });
  expect(result.status).toBe(403);
});

test("AC-04 customer may not resolve their ticket", async ({ app }) => {
  const name = await app.newTicket(app.subject("AC-04"));
  const { observed } = await decide(app, {
    id: "AC-04", role: "customerA", action: "set status to Resolved", route: `PUT ${RESOURCE(name)}`, expected: "denied",
    request: (page) => inApp(page, "PUT", RESOURCE(name), { status: "Resolved" }),
    verify: async () => `stored status ${(await app.stored(name)).status}`,
  });
  expect(observed).toBe("denied");
  expect((await app.stored(name)).status).toBe("Open");
});

test("AC-05 customer may not change the priority", async ({ app }) => {
  const name = await app.newTicket(app.subject("AC-05"));
  const { observed } = await decide(app, {
    id: "AC-05", role: "customerA", action: "change priority", route: `PUT ${RESOURCE(name)}`, expected: "denied",
    request: (page) => inApp(page, "PUT", RESOURCE(name), { priority: "Urgent" }),
    verify: async () => `stored priority ${(await app.stored(name)).priority}`,
  });
  expect(observed).toBe("denied");
  expect((await app.stored(name)).priority).toBe("Medium");
});

test("AC-06 customer may not open the agent desk", async ({ app }) => {
  const name = await app.newTicket(app.subject("AC-06"));
  const page = await openApp(app, "customerA");
  await page.goto(`/helpdesk/tickets/${name}`);
  await page.waitForLoadState("networkidle");
  const agentControls = await page.getByRole("button", { name: /Set Assignee/ }).count();
  await page.screenshot({ path: evidence.screenshotPath("AC-06_customer_agent_desk") });
  evidence.add({
    id: "AC-06", role: "customerA", action: "open the agent ticket screen", route: `GET /helpdesk/tickets/${name}`,
    expected: "denied", observed: agentControls === 0 && !page.url().endsWith(`/helpdesk/tickets/${name}`) ? "denied" : "allowed",
    evidence: `landed on ${new URL(page.url()).pathname}; agent controls shown: ${agentControls} (screens/AC-06_customer_agent_desk.png)`,
  });
  expect(agentControls).toBe(0);
  expect(page.url()).not.toMatch(new RegExp(`/helpdesk/tickets/${name}$`));
});

test("AC-07 customer may not open the Frappe back office", async ({ app }) => {
  const page = await openApp(app, "customerA");
  const response = await page.goto("/app/hd-ticket");
  await page.waitForLoadState("networkidle");
  const listed = await page.getByText("HD Ticket", { exact: false }).count();
  await page.screenshot({ path: evidence.screenshotPath("AC-07_customer_back_office") });
  const path = new URL(page.url()).pathname;
  const observed = path.startsWith("/app/hd-ticket") && listed > 0 ? "allowed" : "denied";
  evidence.add({
    id: "AC-07", role: "customerA", action: "open the back-office ticket list", route: "GET /app/hd-ticket",
    expected: "denied", observed, evidence: `HTTP ${response.status()}, landed on ${path} (screens/AC-07_customer_back_office.png)`,
  });
  expect(observed).toBe("denied");
});

test("AC-08 customer may not assign an agent [finding W-API-05]", async ({ app }) => {
  test.fail(true, "W-API-05: the ticket's own customer can assign an agent");
  const name = await app.newTicket(app.subject("AC-08"));
  const { observed } = await decide(app, {
    id: "AC-08", role: "customerA", action: "assign an agent to own ticket", route: "POST /api/method/run_doc_method (assign_agent)",
    expected: "denied",
    request: (page) => inApp(page, "POST", "/api/method/run_doc_method", {
      dt: "HD Ticket", dn: name, method: "assign_agent", args: { agent: emailOf("agent") },
    }),
    verify: async () => `assignees ${JSON.stringify(await app.assignees(name))}`,
  });
  expect(observed).toBe("denied");
});

// --- Agent ---------------------------------------------------------------------

test("AC-09 agent may read a customer's ticket", async ({ app }) => {
  const name = await app.newTicket(app.subject("AC-09"));
  const { observed } = await decide(app, {
    id: "AC-09", role: "agent", action: "read a customer's ticket", route: `GET ${ONE}`, expected: "allowed",
    request: (page) => inApp(page, "GET", `${ONE}?name=${name}`),
  });
  expect(observed).toBe("allowed");
});

test("AC-10 agent may resolve a ticket", async ({ app }) => {
  const name = await app.newTicket(app.subject("AC-10"));
  const { observed } = await decide(app, {
    id: "AC-10", role: "agent", action: "set status to Resolved", route: `PUT ${RESOURCE(name)}`, expected: "allowed",
    request: (page) => inApp(page, "PUT", RESOURCE(name), { status: "Resolved" }),
    verify: async () => `stored status ${(await app.stored(name)).status}`,
  });
  expect(observed).toBe("allowed");
  expect((await app.stored(name)).status).toBe("Resolved");
});

test("AC-11 agent may assign an agent", async ({ app }) => {
  const name = await app.newTicket(app.subject("AC-11"));
  const { observed } = await decide(app, {
    id: "AC-11", role: "agent", action: "assign an agent", route: "POST /api/method/run_doc_method (assign_agent)", expected: "allowed",
    request: (page) => inApp(page, "POST", "/api/method/run_doc_method", {
      dt: "HD Ticket", dn: name, method: "assign_agent", args: { agent: emailOf("agent") },
    }),
    verify: async () => `assignees ${JSON.stringify(await app.assignees(name))}`,
  });
  expect(observed).toBe("allowed");
  expect(await app.assignees(name)).toEqual([emailOf("agent")]);
});

test("AC-12 agent may not delete a ticket", async ({ app }) => {
  const name = await app.newTicket(app.subject("AC-12"));
  const { observed } = await decide(app, {
    id: "AC-12", role: "agent", action: "delete a ticket", route: `DELETE ${RESOURCE(name)}`, expected: "denied",
    request: (page) => inApp(page, "DELETE", RESOURCE(name)),
    verify: async () => `ticket still stored: ${Boolean((await app.stored(name)).name)}`,
  });
  expect(observed).toBe("denied");
});

// --- Not signed in -------------------------------------------------------------

test("AC-13 a visitor who is not signed in may not read a ticket", async ({ app }) => {
  const name = await app.newTicket(app.subject("AC-13"));
  const page = await app.pageAs(null);
  await page.goto("/login");
  const result = await inApp(page, "GET", `${ONE}?name=${name}`, undefined, { csrf: false });
  evidence.add({
    id: "AC-13", role: "anonymous", action: "read a ticket", route: `GET ${ONE}`, expected: "denied",
    observed: result.status === 200 ? "allowed" : "denied", evidence: `HTTP ${result.status} ${reason(result)}`,
  });
  expect(result.status).toBe(403);
});
