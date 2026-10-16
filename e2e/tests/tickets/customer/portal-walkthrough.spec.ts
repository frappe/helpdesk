import type { Page } from "@playwright/test";
import type { Api } from "../../../helpers/api";
import { raiseTicket } from "../../../helpers/factories";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";

// Every action on the portal ticket page (/help/tickets/:id), past what portal-conversation covers.
usePersona("customer");

async function agentReply(agent: Api, ticket: string, html: string) {
  await agent.call("run_doc_method", {
    dt: "HD Ticket",
    dn: ticket,
    method: "reply_via_agent",
    args: { message: html },
  });
}

/** Email bodies render inside iframes; the frame that shows `text` (never the page's own composer). */
async function frameWith(page: Page, text: string) {
  const frames = () => page.frames().filter((frame) => frame !== page.mainFrame());
  await expect
    .poll(async () => {
      for (const frame of frames()) if (await frame.getByText(text).count()) return true;
      return false;
    })
    .toBe(true);
  for (const frame of frames()) if (await frame.getByText(text).count()) return frame;
  throw new Error(`no frame shows ${text}`);
}

/** The header's Close, not the X of a dialog that shares its name. */
function closeButton(page: Page) {
  return page.getByRole("button", { name: "Close", exact: true }).first();
}

function composer(page: Page) {
  return page.locator(".portal-reply-composer .ProseMirror");
}

// Closed on arrival; its bar opens it.
async function openComposer(page: Page) {
  await page.getByText("Type a message").click();
  return composer(page);
}

async function communication(api: Api, ticket: string, text: string) {
  const rows = await api.list("Communication", {
    filters: { reference_doctype: "HD Ticket", reference_name: ticket },
    fields: ["name", "sender", "content"],
  });
  return rows.find((row) => row.content.includes(text));
}

test.describe("access", () => {
  test("someone else's ticket, or none, reads as not found", async ({ page, apiAs }) => {
    const colleague = await raiseTicket(await apiAs("customerManager"));
    for (const name of [colleague.name, "99999999"]) {
      await page.goto(`/help/tickets/${name}`);
      await expect(page.getByText("Ticket not found")).toBeVisible();
      await expect(
        page.getByText("It may have been removed, or you may not have access to it.")
      ).toBeVisible();
    }
  });
});

test.describe("conversation", () => {
  test("agent emails are sandboxed: links open a new tab, scripts are stripped, quotes fold", async ({
    page,
    apiAs,
    ticket,
  }) => {
    const marker = `Sandboxed ${uid()}`;
    await agentReply(
      await apiAs("agent"),
      ticket.name,
      `<p>${marker} <a href="https://example.com/doc">the doc</a></p>
       <img src="x" onerror="window.__e2eXss=1"><script>window.__e2eXss=1</script>
       <div class="gmail_quote">Quoted ${marker}</div>`
    );
    await page.goto(`/help/tickets/${ticket.name}`);
    const frame = await frameWith(page, marker);
    // a link opens a new tab, by its own target or the frame's <base target>
    const target = await frame.getByRole("link", { name: "the doc" }).evaluate(
      (link: HTMLAnchorElement) => link.target || document.querySelector("base")?.target || ""
    );
    expect(target).toBe("_blank");
    expect(await frame.locator("body script").count()).toBe(0);
    expect(await frame.locator("[onerror]").count()).toBe(0);
    expect(await page.evaluate(() => (window as any).__e2eXss)).toBeUndefined();

    const quote = frame.getByText(`Quoted ${marker}`);
    await expect(quote).toBeHidden();
    await frame.getByRole("button").filter({ hasText: "..." }).or(frame.getByText("...", { exact: true })).first().click();
    await expect(quote).toBeVisible();
  });

  test("whitespace alone cannot be sent", async ({ page, ticket }) => {
    await page.goto(`/help/tickets/${ticket.name}`);
    await (await openComposer(page)).fill("   ");
    await expect(page.getByRole("button", { name: "Send" })).toBeDisabled();
  });

  test("a reply to a resolved ticket reopens it; there is no separate reopen", async ({ page, api, ticket }) => {
    await api.update("HD Ticket", ticket.name, { status: "Resolved" });
    await page.goto(`/help/tickets/${ticket.name}`);
    await expect(page.getByRole("button", { name: /Reopen/ })).toHaveCount(0);
    const reply = `Still broken ${uid()}`;
    await (await openComposer(page)).fill(reply);
    await page.getByRole("button", { name: "Send" }).click();
    await frameWith(page, reply);
    await expect.poll(async () => (await api.get("HD Ticket", ticket.name)).status).toBe("Open");
  });

  test("a reply carries an attached file", async ({ page, api, ticket }) => {
    await page.goto(`/help/tickets/${ticket.name}`);
    await openComposer(page);
    const chooser = page.waitForEvent("filechooser");
    await page.getByRole("button", { name: "Attach file" }).click();
    await (await chooser).setFiles({ name: "log.txt", mimeType: "text/plain", buffer: Buffer.from("trace") });
    await expect(page.getByText("log.txt")).toBeVisible();
    const reply = `With a log ${uid()}`;
    await composer(page).fill(reply);
    await page.getByRole("button", { name: "Send" }).click();
    await frameWith(page, reply);
    await expect.poll(() => communication(api, ticket.name, reply)).toBeTruthy();
    const sent = (await communication(api, ticket.name, reply))!;
    await expect
      .poll(async () =>
        (await api.list("File", {
          filters: { attached_to_doctype: "Communication", attached_to_name: sent.name },
          fields: ["file_name"],
        })).map((file) => file.file_name)
      )
      .toEqual(["log.txt"]);
  });

  test("the composer collapses after sending and reopens from its bar", async ({ page, ticket }) => {
    await page.goto(`/help/tickets/${ticket.name}`);
    const reply = `Collapse ${uid()}`;
    await (await openComposer(page)).fill(reply);
    await page.getByRole("button", { name: "Send" }).click();
    await frameWith(page, reply);
    await expect(composer(page)).toBeHidden();
    const bar = page.getByText("Type a message");
    await bar.click();
    await expect(composer(page)).toBeVisible();
  });

  test("the composer resizes from the keyboard and keeps its height", async ({ page, ticket }) => {
    await page.goto(`/help/tickets/${ticket.name}`);
    await openComposer(page);
    const handle = page.getByRole("separator", { name: "Resize composer" });
    await handle.focus();
    await page.keyboard.press("ArrowUp");
    await page.keyboard.press("ArrowUp");
    const stored = await page.evaluate(() => localStorage.getItem("kb:composer-height"));
    expect(Number(stored)).toBeGreaterThan(0);
    await page.reload();
    await openComposer(page);
    await expect(page.getByRole("separator", { name: "Resize composer" })).toBeVisible();
    expect(await page.evaluate(() => localStorage.getItem("kb:composer-height"))).toBe(stored);
  });

  // Env: the socket server resolves the site from the Host header, and localhost:8020 is not e2e.localhost,
  // so no realtime event reaches the page here. Runs where the site is served under its own name.
  test.fixme("an agent's reply elsewhere shows without a reload", async ({ page, apiAs, ticket }) => {
    await page.goto(`/help/tickets/${ticket.name}`);
    await expect(closeButton(page)).toBeVisible();
    const live = `Live ${uid()}`;
    await agentReply(await apiAs("agent"), ticket.name, `<p>${live}</p>`);
    await frameWith(page, live);
  });
});

test.describe("layouts", () => {
  async function useChat(page: Page) {
    await page.addInitScript(() => localStorage.setItem("kb:conversation-layout", "chat"));
  }

  async function centreX(page: Page, frameText: string) {
    for (const frame of page.frames()) {
      if (!(await frame.getByText(frameText).count())) continue;
      const box = await (await frame.frameElement()).boundingBox();
      return box!.x + box!.width / 2;
    }
    throw new Error(frameText);
  }

  test("chat: the customer's messages on the right, the agent's on the left; closes are dividers", async ({
    page,
    api,
    apiAs,
    ticket,
  }) => {
    const answer = `Chat answer ${uid()}`;
    await agentReply(await apiAs("agent"), ticket.name, `<p>${answer}</p>`);
    await api.update("HD Ticket", ticket.name, { status: "Closed" });
    await api.update("HD Ticket", ticket.name, { status: "Open" });
    await useChat(page);
    await page.goto(`/help/tickets/${ticket.name}`);
    await frameWith(page, answer);
    const width = page.viewportSize()!.width;
    expect(await centreX(page, `${ticket.subject} description`)).toBeGreaterThan(width / 3);
    expect(await centreX(page, answer)).toBeLessThan(width / 3);
    await expect(page.getByText(/^Closed by /)).toBeVisible();
    await expect(page.getByText(/^Reopened by /)).toBeVisible();
  });

  test("timeline: closes and reopens read as log rows", async ({ page, api, ticket }) => {
    await api.update("HD Ticket", ticket.name, { status: "Closed" });
    await api.update("HD Ticket", ticket.name, { status: "Open" });
    await page.goto(`/help/tickets/${ticket.name}`);
    await expect(page.getByText(/ closed the ticket/)).toBeVisible();
    await expect(page.getByText(/ reopened the ticket/)).toBeVisible();
  });

  test("chat: an agent's own replies sit on the right", async ({ pageAs, apiAs, ticket }) => {
    const answer = `Own reply ${uid()}`;
    await agentReply(await apiAs("agent"), ticket.name, `<p>${answer}</p>`);
    const page = await pageAs("agent");
    await useChat(page);
    await page.goto(`/help/tickets/${ticket.name}`);
    await frameWith(page, answer);
    expect(await centreX(page, answer)).toBeGreaterThan(page.viewportSize()!.width / 3);
  });
});

test.describe("details panel", () => {

  test("timeline steps: received, first response due, resolution due", async ({ page, ticket }) => {
    await page.goto(`/help/tickets/${ticket.name}`);
    await expect(page.getByText("Request received")).toBeVisible();
    await expect(page.getByText("First response")).toBeVisible();
    await expect(page.getByText("Resolution")).toBeVisible();
    await expect(page.getByText(/^Due /).first()).toBeVisible();
  });

  test("a paused status puts the next step on hold", async ({ page, api, ticket }) => {
    await api.update("HD Ticket", ticket.name, { status: "Replied" });
    await page.goto(`/help/tickets/${ticket.name}`);
    await expect(page.getByText("On hold")).toBeVisible();
  });
});
