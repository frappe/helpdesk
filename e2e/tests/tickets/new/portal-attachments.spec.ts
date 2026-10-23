import { mkdtempSync, rmSync, truncateSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import type { Page } from "@playwright/test";
import type { Api } from "../../../helpers/api";
import { ensureTemplate } from "../../../helpers/form-script";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";

usePersona("customer");

const UPLOAD = "**/api/method/upload_file";
const MB = 1024 * 1024;

async function useUrlMethodField(api: Api) {
  await ensureTemplate(api);
  const before = await api.get("HD Ticket Template", "Default");
  await api.update("HD Ticket Template", "Default", {
    fields: [{ fieldname: "e2e_needed", url_method: "helpdesk.e2e_options", visible_to: "Everyone", required: 1 }],
  });
  return () => api.update("HD Ticket Template", "Default", { fields: before.fields });
}

async function openUrlMethodField(page: Page) {
  await page.goto("/help/my-tickets/new");
  await page
    .getByRole("button", { name: /^E2E needed/ })
    .or(page.getByRole("combobox", { name: /^E2E needed/ }))
    .first()
    .click();
}

function attach(page: Page, files: { name: string; mimeType: string; buffer: Buffer }) {
  return page.locator("input[type=file].sr-only").setInputFiles(files);
}

function row(page: Page, name: string) {
  return page.locator("div.flex.items-center.gap-3").filter({ hasText: name });
}

test.describe("url_method options", () => {
  test("a failing url_method shows an error, not an empty list", async ({ page, api }) => {
    const restore = await useUrlMethodField(api);
    const errors: Error[] = [];
    page.on("pageerror", (error) => errors.push(error));
    await page.route("**/api/method/helpdesk.e2e_options*", (route) =>
      route.fulfill({ status: 500, json: { exc_type: "Exception" } })
    );
    try {
      await openUrlMethodField(page);
      await expect(page.getByText("Could not load the options")).toBeVisible();
      expect(errors).toEqual([]);
    } finally {
      await restore();
    }
  });

  test("a slow url_method shows a loading state", async ({ page, api }) => {
    const restore = await useUrlMethodField(api);
    let release = () => {};
    await page.route("**/api/method/helpdesk.e2e_options*", async (route) => {
      await new Promise<void>((resolve) => (release = resolve));
      await route.fulfill({ json: { message: ["Red"] } });
    });
    try {
      await openUrlMethodField(page);
      await expect(page.getByText("Loading...")).toBeVisible();
      await expect(page.getByText("No results")).toHaveCount(0);
      release();
      await expect(page.getByRole("option", { name: "Red" })).toBeVisible();
    } finally {
      await restore();
    }
  });
});

test.describe("upload messages", () => {
  test("server errors show as plain text", async ({ page }) => {
    await page.route(UPLOAD, (route) =>
      route.fulfill({
        status: 417,
        json: {
          exc_type: "ValidationError",
          _server_messages: JSON.stringify([JSON.stringify({ message: "<strong>File Name</strong> is too long" })]),
        },
      })
    );
    await page.goto("/help/my-tickets/new");
    await attach(page, { name: "long.txt", mimeType: "text/plain", buffer: Buffer.from("x") });
    await expect(row(page, "long.txt").getByText("File Name is too long")).toBeVisible();
    await expect(page.getByText("<strong>")).toHaveCount(0);
  });

  test("an empty file is refused before upload", async ({ page }) => {
    let uploads = 0;
    page.on("request", (request) => request.url().includes("upload_file") && uploads++);
    await page.goto("/help/my-tickets/new");
    await attach(page, { name: "empty.txt", mimeType: "text/plain", buffer: Buffer.alloc(0) });
    await expect(page.getByText('"empty.txt" was skipped — the file is empty.')).toBeVisible();
    expect(uploads).toBe(0);
  });

  test("a tiny file shows its size in bytes", async ({ page }) => {
    await page.goto("/help/my-tickets/new");
    await attach(page, { name: "one.txt", mimeType: "text/plain", buffer: Buffer.from("x") });
    await expect(row(page, "one.txt").getByText("1 B", { exact: true })).toBeVisible();
  });

  test("a file name over 140 characters uploads under a shortened name", async ({ page, api }) => {
    const stem = `long-${uid()}-`;
    for (const length of [200, 260]) {
      const name = `${stem}${"y".repeat(length)}.txt`;
      await page.goto("/help/my-tickets/new");
      await attach(page, { name, mimeType: "text/plain", buffer: Buffer.from(name) });
      await expect(row(page, stem).getByText("Upload failed")).toHaveCount(0);
      await expect(row(page, stem).getByRole("link")).toBeVisible();
      const saved = await api.list("File", { filters: { file_name: ["like", `${stem}%`] }, fields: ["file_name"] });
      expect(saved.map((file) => file.file_name)).toContainEqual(`${stem}${"y".repeat(134 - stem.length - 4)}.txt`);
    }
  });
});

test.describe("pasting", () => {
  test("a non-image file pasted in the editor is attached", async ({ page }) => {
    await page.goto("/help/my-tickets/new");
    await page.locator(".ProseMirror").click();
    await page.evaluate(() => {
      const data = new DataTransfer();
      data.items.add(new File(["%PDF-1.4"], "report.pdf", { type: "application/pdf" }));
      document
        .querySelector(".ProseMirror")!
        .dispatchEvent(new ClipboardEvent("paste", { clipboardData: data, bubbles: true }));
    });
    await expect(row(page, "report.pdf")).toBeVisible();
  });
});

test.describe("size limit", () => {
  test("a file over the site limit is refused before upload", async ({ page, api }) => {
    const limit: number = await api.call("frappe.core.api.file.get_max_file_size");
    const dir = mkdtempSync(join(tmpdir(), "e2e-"));
    // Just under the limit: the multipart wrapping would push the request over it.
    const big = join(dir, "big.txt");
    writeFileSync(big, "");
    truncateSync(big, limit - 100);
    let uploads = 0;
    page.on("request", (request) => request.url().includes("upload_file") && uploads++);
    try {
      await page.goto("/help/my-tickets/new");
      await page.locator("input[type=file].sr-only").setInputFiles(big);
      await expect(row(page, "big.txt").getByText(`File is larger than ${limit / MB} MB`)).toBeVisible();
      expect(uploads).toBe(0);
    } finally {
      rmSync(dir, { recursive: true });
    }
  });

  test("a 413 from the server shows the size limit", async ({ page, api }) => {
    const limit: number = await api.call("frappe.core.api.file.get_max_file_size");
    await page.route(UPLOAD, (route) => route.fulfill({ status: 413, body: "Request Entity Too Large" }));
    await page.goto("/help/my-tickets/new");
    await attach(page, { name: "huge.txt", mimeType: "text/plain", buffer: Buffer.from("x") });
    await expect(row(page, "huge.txt").getByText(`File is larger than ${limit / MB} MB`)).toBeVisible();
  });
});

test.describe("orphan files", () => {
  test("removing a row mid-upload deletes the File the server saved", async ({ page, api }) => {
    const name = `late-${uid()}.txt`;
    await page.goto("/help/my-tickets/new");
    await expect(page.getByText("Drag or paste files here, or click to browse")).toBeVisible();
    // A trickling download holds the response back after the server has saved the File.
    const cdp = await page.context().newCDPSession(page);
    await cdp.send("Network.emulateNetworkConditions", {
      offline: false,
      latency: 0,
      downloadThroughput: 20,
      uploadThroughput: -1,
    });
    await attach(page, { name, mimeType: "text/plain", buffer: Buffer.from("late") });
    await expect.poll(() => api.exists("File", { file_name: name })).toBeTruthy();
    const saved = (await api.exists("File", { file_name: name }))!;
    await row(page, name).getByRole("button", { name: "Cancel upload" }).click();
    await expect(row(page, name)).toHaveCount(0);
    await cdp.send("Network.emulateNetworkConditions", {
      offline: false,
      latency: 0,
      downloadThroughput: -1,
      uploadThroughput: -1,
    });
    await expect.poll(() => api.exists("File", { name: saved }), { timeout: 30_000 }).toBeUndefined();
  });

  test("leaving the form without creating deletes its uploads", async ({ page, api }) => {
    const name = `left-${uid()}.txt`;
    await page.goto("/help/my-tickets");
    await page.getByRole("button", { name: "Raise a ticket" }).click();
    await attach(page, { name, mimeType: "text/plain", buffer: Buffer.from("left") });
    await expect.poll(() => api.exists("File", { file_name: name })).toBeTruthy();
    await expect(row(page, name).getByRole("button", { name: "Cancel upload" })).toHaveCount(0);
    await page.goBack();
    await expect(page).toHaveURL(/\/help\/my-tickets$/);
    await expect.poll(() => api.exists("File", { file_name: name })).toBeUndefined();
  });
});
