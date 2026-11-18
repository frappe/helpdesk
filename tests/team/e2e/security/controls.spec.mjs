// Security controls observed through the running app. Each check is also
// corroborated against the framework source in ../../security/SECURITY_REPORT.md.
import { expect, test } from "../support/app.mjs";
import { Evidence, inApp, openApp, reason } from "../support/security.mjs";

const NEW = "/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.new";
const ONE = "/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.get_one";
const evidence = new Evidence("controls");

test.describe.configure({ mode: "serial" });
test.afterAll(() => evidence.write());

test("CT-01 session cookie attributes", async ({ app }) => {
  const page = await openApp(app, "customerA");
  const sid = (await page.context().cookies()).find((c) => c.name === "sid");
  evidence.add({
    id: "CT-01", control: "session cookie", check: "sid is HttpOnly, SameSite=Lax, Secure",
    expected: "HttpOnly true, SameSite Lax, Secure true when served over HTTPS",
    observed: `HttpOnly ${sid.httpOnly}, SameSite ${sid.sameSite}, Secure ${sid.secure} (site served over plain HTTP), expires in ${Math.round((sid.expires - Date.now() / 1000) / 3600)} h`,
    result: sid.httpOnly && sid.sameSite === "Lax" ? "pass (Secure not testable without HTTPS)" : "fail",
  });
  expect(sid.httpOnly).toBe(true);
  expect(sid.sameSite).toBe("Lax");
  // the cookie is not readable by page scripts
  expect(await page.evaluate(() => document.cookie.includes("sid="))).toBe(false);
});

test("CT-02 CSRF token is required for a state change from a browser session", async ({ app }) => {
  const page = await openApp(app, "customerA");
  const before = await app.ticketCount();
  const subject = app.subject("CT-02");
  const without = await inApp(page, "POST", NEW, { doc: { subject, description: "<p>x</p>" } }, { csrf: false });
  const afterWithout = await app.ticketCount();
  const withToken = await inApp(page, "POST", NEW, { doc: { subject, description: "<p>x</p>" } });
  evidence.add({
    id: "CT-02", control: "CSRF token", check: "POST /api new ticket without, then with, X-Frappe-CSRF-Token",
    expected: "without token: rejected, nothing created; with token: created",
    observed: `without: HTTP ${without.status} ${reason(without)}; tickets ${before} -> ${afterWithout}; with: HTTP ${withToken.status}`,
    result: without.status !== 200 && afterWithout === before && withToken.status === 200 ? "pass" : "fail",
  });
  expect(without.status).toBe(400);
  expect(afterWithout).toBe(before);
  expect(withToken.status).toBe(200);
});

test("CT-03 signing out ends the session on the server", async ({ app }) => {
  const name = await app.newTicket(app.subject("CT-03"));
  const page = await openApp(app, "customerA");
  const sid = (await page.context().cookies()).find((c) => c.name === "sid").value;
  const before = await inApp(page, "GET", `${ONE}?name=${name}`);
  await inApp(page, "POST", "/api/method/logout", {});
  // replay the old session id, as a stolen cookie would be
  const replay = await page.context().request.get(`${ONE}?name=${name}`, { headers: { Cookie: `sid=${sid}` } });
  evidence.add({
    id: "CT-03", control: "session end", check: "replay the sid cookie after logout",
    expected: "old session id no longer grants access",
    observed: `before logout HTTP ${before.status}; replayed sid after logout HTTP ${replay.status()}`,
    result: before.status === 200 && [401, 403].includes(replay.status()) ? "pass" : "fail",
  });
  expect(before.status).toBe(200);
  expect([401, 403]).toContain(replay.status());
});

test("CT-04 failed sign-in does not reveal whether the account exists", async ({ app, playwright, baseURL }) => {
  const request = await playwright.request.newContext({ baseURL });
  const known = await request.post("/api/method/login", { data: { usr: "customer.a@sqe.test", pwd: "wrong-password-1" } });
  const unknown = await request.post("/api/method/login", { data: { usr: "nobody.here@sqe.test", pwd: "wrong-password-1" } });
  const knownMessage = (await known.json()).message;
  const unknownMessage = (await unknown.json()).message;
  evidence.add({
    id: "CT-04", control: "sign-in errors", check: "wrong password for an existing account vs an unknown account",
    expected: "same status and same message",
    observed: `existing: HTTP ${known.status()} "${knownMessage}"; unknown: HTTP ${unknown.status()} "${unknownMessage}"`,
    result: known.status() === unknown.status() && knownMessage === unknownMessage ? "pass" : "fail",
  });
  await request.dispose();
  expect(known.status()).toBe(unknown.status());
  expect(knownMessage).toBe(unknownMessage);
});

test("CT-05 role checks are enforced by the server, not only by hiding controls", async ({ app }) => {
  // The customer screen shows no priority control (UC-03 EF2); the same change
  // sent directly must still be refused by the server.
  const name = await app.newTicket(app.subject("CT-05"));
  const page = await openApp(app, "customerA");
  await page.goto(`/helpdesk/my-tickets/${name}`);
  const controlShown = await page.getByRole("combobox", { name: /Priority/ }).count();
  const direct = await inApp(page, "PUT", `/api/resource/HD Ticket/${name}`, { priority: "Urgent" });
  const stored = (await app.stored(name)).priority;
  evidence.add({
    id: "CT-05", control: "server-side role check", check: "customer sends a priority change the screen does not offer",
    expected: "no control on screen, and the direct request refused",
    observed: `priority control shown: ${controlShown}; direct PUT HTTP ${direct.status} ${reason(direct)}; stored priority ${stored}`,
    result: controlShown === 0 && direct.status === 403 && stored === "Medium" ? "pass" : "fail",
  });
  expect(controlShown).toBe(0);
  expect(direct.status).toBe(403);
  expect(stored).toBe("Medium");
});

// DEF-14 (SEC-02): the HTML sanitiser in the served bundle must have no
// published advisory. OSV lists eight advisories for DOMPurify 3.4.8; the last
// of them is fixed in 3.4.17, so that is the lowest acceptable version.
const DOMPURIFY_MIN = [3, 4, 17];
const atLeast = (version, min) => {
  const parts = version.split(".").map(Number);
  for (let i = 0; i < min.length; i++) if (parts[i] !== min[i]) return parts[i] > min[i];
  return true;
};

test("CT-08 the HTML sanitiser served to the browser has no known advisory", async ({ app }) => {
  const page = await app.pageAs("customerA");
  const scripts = new Set();
  page.on("response", (response) => {
    if (response.request().resourceType() === "script" && response.url().includes("/assets/helpdesk/")) {
      scripts.add(response.url());
    }
  });
  await page.goto("/helpdesk/my-tickets");
  await page.waitForLoadState("networkidle");
  const versions = new Set();
  for (const url of scripts) {
    const body = await (await page.request.get(url)).text();
    for (const match of body.matchAll(/DOMPurify ([0-9]+\.[0-9]+\.[0-9]+)/g)) versions.add(match[1]);
  }
  const found = [...versions];
  const ok = found.length > 0 && found.every((v) => atLeast(v, DOMPURIFY_MIN));
  evidence.add({
    id: "CT-08", control: "vulnerable components", check: "DOMPurify version embedded in the served Helpdesk scripts",
    expected: `DOMPurify ${DOMPURIFY_MIN.join(".")} or later (no OSV advisory)`,
    observed: `${scripts.size} Helpdesk scripts loaded; DOMPurify ${found.join(", ") || "not found"}`,
    result: ok ? "pass" : "fail: SEC-02",
  });
  expect(found.length, "DOMPurify was not found in the served scripts").toBeGreaterThan(0);
  for (const version of found) expect(atLeast(version, DOMPURIFY_MIN), `DOMPurify ${version}`).toBe(true);
});
