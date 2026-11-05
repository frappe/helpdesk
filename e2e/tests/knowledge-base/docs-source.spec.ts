import type { Page } from "@playwright/test";
import { expect, test, usePersona } from "../../helpers/fixtures";

usePersona("manager");

const GET = "**/api/method/helpdesk.api.docs_source.get_docs_source*";
const CONNECT = "**/api/method/helpdesk.api.docs_source.connect_docs_source*";
const HIDE = "**/api/method/helpdesk.api.docs_source.set_hidden_sections*";

const BASE = {
  url: "https://docs.example.com",
  sections: [],
  sections_error: false,
  page_count: 0,
  synced_on: null,
  truncated: false,
  error: "",
  syncing: false,
};
const WIKI = {
  ...BASE,
  type: "Frappe Wiki",
  label: "Frappe Wiki",
  sections: [
    { key: "guides", title: "Guides", hidden: false },
    { key: "legal", title: "Legal", hidden: false },
  ],
};
const INDEXED = {
  ...BASE,
  type: "llms.txt",
  label: "docs.example.com",
  page_count: 142,
  synced_on: new Date(Date.now() - 3 * 86400_000).toISOString().replace("T", " ").slice(0, 19),
};

const json = (message: unknown) => ({ json: { message } });

async function open(page: Page, source: unknown) {
  await page.route(GET, (route) => route.fulfill(json(source)));
  await page.goto("/help/settings/knowledge-base");
  const dialog = page.getByRole("dialog", { name: "Settings" });
  await expect(dialog.getByRole("heading", { name: "Docs source" })).toBeVisible();
  return dialog;
}

test("wiki shows section checkboxes and unticking saves at once", async ({ page }) => {
  const dialog = await open(page, WIKI);
  let sent: any;
  await page.route(HIDE, (route) => {
    sent = route.request().postDataJSON();
    return route.fulfill(json(null));
  });
  await expect(dialog.getByRole("checkbox", { name: "Guides" })).toBeChecked();
  await dialog.getByRole("checkbox", { name: "Legal" }).uncheck();
  await expect.poll(() => sent?.sections).toEqual(["legal"]);
  await expect(dialog.getByRole("checkbox", { name: "Legal" })).not.toBeChecked();
});

test("a failed save restores the box and shows the error", async ({ page }) => {
  const dialog = await open(page, WIKI);
  await page.route(HIDE, (route) =>
    route.fulfill({
      status: 417,
      json: { exc_type: "ValidationError", _server_messages: JSON.stringify([JSON.stringify({ message: "Nope, not now" })]) },
    })
  );
  await dialog.getByRole("checkbox", { name: "Legal" }).uncheck();
  await expect(dialog.getByText("Nope, not now")).toBeVisible();
  await expect(dialog.getByRole("checkbox", { name: "Legal" })).toBeChecked();
});

test("unreadable wiki sections show a message, not an empty list", async ({ page }) => {
  const dialog = await open(page, { ...WIKI, sections: [], sections_error: true });
  await expect(dialog.getByText("The sections could not be read right now.")).toBeVisible();
  await expect(dialog.getByRole("checkbox")).toHaveCount(0);
});

test("indexed source shows Resync and the page line", async ({ page }) => {
  const dialog = await open(page, { ...INDEXED, truncated: true });
  await expect(dialog.getByRole("button", { name: "Resync" })).toBeVisible();
  await expect(dialog.getByText(/142 pages · synced 3 days ago/)).toBeVisible();
  await expect(dialog.getByText(/not all pages/i)).toBeVisible();
  await expect(dialog.getByRole("checkbox")).toHaveCount(0);
});

test("a sync error shows the server text", async ({ page }) => {
  const dialog = await open(page, { ...INDEXED, error: "The site refused the read." });
  await expect(dialog.getByText("The site refused the read.")).toBeVisible();
});

test("connect on an indexed site polls until the sync ends", async ({ page }) => {
  let polls = 0;
  let connected = false;
  await page.route(GET, (route) => {
    if (!connected) return route.fulfill(json(null));
    polls++;
    return route.fulfill(
      json(polls < 2 ? { ...INDEXED, synced_on: null, page_count: 0, syncing: true } : INDEXED)
    );
  });
  await page.route(CONNECT, (route) => {
    connected = true;
    return route.fulfill(json({ ...INDEXED, synced_on: null, page_count: 0, syncing: false }));
  });
  await page.goto("/help/settings/knowledge-base");
  const dialog = page.getByRole("dialog", { name: "Settings" });
  await dialog.getByPlaceholder("https://docs.example.com").fill("https://docs.example.com");
  await dialog.getByRole("button", { name: "Connect" }).click();
  await expect(dialog.getByRole("button", { name: /Syncing/ })).toBeVisible();
  await expect(dialog.getByText(/142 pages/)).toBeVisible({ timeout: 15_000 });
  await expect(dialog.getByRole("button", { name: "Resync" })).toBeVisible();
});

test.describe("plain agent", () => {
  test.use({ storageState: "e2e/.auth/agent.json" });

  test("does not see the Docs source section", async ({ page }) => {
    await page.goto("/help/settings/knowledge-base");
    await expect(page.getByRole("dialog", { name: "Settings" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Docs source" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Connect" })).toHaveCount(0);
  });
});
