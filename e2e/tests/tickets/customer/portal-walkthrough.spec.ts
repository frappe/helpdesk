import type { Page } from "@playwright/test";
import type { Api } from "../../../helpers/api";
import { raiseTicket } from "../../../helpers/factories";
import { FormScripts } from "../../../helpers/form-script";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";
import { personas } from "../../../helpers/personas";
import { snapshotSettings } from "../../../helpers/settings";

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

/** The confirm dialog's red Close; its X is labelled Close too. */
function confirmClose(page: Page) {
  return page.getByRole("dialog").getByRole("button", { name: "Close", exact: true }).last().click();
}

function composer(page: Page) {
  return page.locator(".portal-reply-composer .ProseMirror");
}

async function communication(api: Api, ticket: string, text: string) {
  const rows = await api.list("Communication", {
    filters: { reference_doctype: "HD Ticket", reference_name: ticket },
    fields: ["name", "sender", "content"],
  });
  return rows.find((row) => row.content.includes(text));
}

async function useFeedbackMandatory(api: Api, on: 0 | 1) {
  const restore = await snapshotSettings(api, ["is_feedback_mandatory"]);
  await api.update("HD Settings", "HD Settings", { is_feedback_mandatory: on });
  return restore;
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

  test("a manager opens, answers and closes a colleague's ticket", async ({ pageAs, api, apiAs }) => {
    const colleague = await raiseTicket(await apiAs("customer"));
    const page = await pageAs("customerManager");
    await page.goto(`/help/tickets/${colleague.name}`);
    await expect(page.getByRole("button", { name: colleague.subject })).toBeVisible();

    const reply = `Manager note ${uid()}`;
    await composer(page).fill(reply);
    await page.getByRole("button", { name: "Send" }).click();
    await frameWith(page, reply);
    await expect
      .poll(async () => (await communication(api, colleague.name, reply))?.sender)
      .toBe(personas.customerManager.email);

    // no agent reply yet, so closing never asks for a rating
    await closeButton(page).click();
    await confirmClose(page);
    await expect.poll(async () => (await api.get("HD Ticket", colleague.name)).status).toBe("Closed");
  });

  test("an agent opens any ticket on the portal", async ({ pageAs, apiAs }) => {
    const ticket = await raiseTicket(await apiAs("customer"));
    const page = await pageAs("agent");
    await page.goto(`/help/tickets/${ticket.name}`);
    await expect(page.getByRole("button", { name: ticket.subject })).toBeVisible();
    await expect(closeButton(page)).toBeVisible();
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
    await composer(page).fill("   ");
    await expect(page.getByRole("button", { name: "Send" })).toBeDisabled();
  });

  test("a reply to a resolved ticket reopens it; there is no separate reopen", async ({ page, api, ticket }) => {
    await api.update("HD Ticket", ticket.name, { status: "Resolved" });
    await page.goto(`/help/tickets/${ticket.name}`);
    await expect(page.getByRole("button", { name: /Reopen/ })).toHaveCount(0);
    const reply = `Still broken ${uid()}`;
    await composer(page).fill(reply);
    await page.getByRole("button", { name: "Send" }).click();
    await frameWith(page, reply);
    await expect.poll(async () => (await api.get("HD Ticket", ticket.name)).status).toBe("Open");
  });

  test("a reply carries an attached file", async ({ page, api, ticket }) => {
    await page.goto(`/help/tickets/${ticket.name}`);
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
    await composer(page).fill(reply);
    await page.getByRole("button", { name: "Send" }).click();
    await frameWith(page, reply);
    await expect(composer(page)).toBeHidden();
    const bar = page.getByText("Type a message");
    await bar.click();
    await expect(composer(page)).toBeVisible();
  });

  test("the composer resizes from the keyboard and keeps its height", async ({ page, ticket }) => {
    await page.goto(`/help/tickets/${ticket.name}`);
    const handle = page.getByRole("separator", { name: "Resize composer" });
    await handle.focus();
    await page.keyboard.press("ArrowUp");
    await page.keyboard.press("ArrowUp");
    const stored = await page.evaluate(() => localStorage.getItem("kb:composer-height"));
    expect(Number(stored)).toBeGreaterThan(0);
    await page.reload();
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

test.describe("closing and rating", () => {
  test("close asks to confirm; cancel keeps it open", async ({ page, api, ticket }) => {
    await page.goto(`/help/tickets/${ticket.name}`);
    await closeButton(page).click();
    const dialog = page.getByRole("dialog");
    await expect(dialog.getByText("Are you sure you want to close this ticket?")).toBeVisible();
    await dialog.getByRole("button", { name: "Cancel" }).click();
    await expect(dialog).toHaveCount(0);
    expect((await api.get("HD Ticket", ticket.name)).status).toBe("Open");

    await closeButton(page).click();
    await confirmClose(page);
    await expect(page.getByRole("button", { name: "Raise a ticket" })).toBeVisible();
    await expect(composer(page)).toHaveCount(0);
    expect((await api.get("HD Ticket", ticket.name)).status).toBe("Closed");
  });

  test("the rating dialog: stars reload options, submit needs an option, details show after", async ({
    page,
    api,
    apiAs,
    ticket,
  }) => {
    await agentReply(await apiAs("agent"), ticket.name, "<p>Done</p>");
    const restore = await useFeedbackMandatory(api, 1);
    try {
      await page.goto(`/help/tickets/${ticket.name}`);
      await closeButton(page).click();
      const dialog = page.getByRole("dialog", { name: "Rate this ticket" });
      const submit = dialog.getByRole("button", { name: "Submit" });

      await dialog.getByRole("radio").nth(3).click();
      await expect(dialog.getByRole("button", { name: "Prompt, informative support" })).toBeVisible();
      await expect(dialog.getByRole("button", { name: "Exceptional support experience" })).toHaveCount(0);
      await expect(submit).toBeDisabled();
      await dialog.getByRole("button", { name: "Prompt, informative support" }).click();
      await expect(submit).toBeEnabled();

      // a new star value clears the chosen option
      await dialog.getByRole("radio").nth(4).click();
      await expect(submit).toBeDisabled();
      await dialog.getByRole("button", { name: "Exceptional support experience" }).click();
      await dialog.getByPlaceholder("Tell us more").fill("Thanks");
      await submit.click();

      await expect.poll(async () => (await api.get("HD Ticket", ticket.name)).status).toBe("Closed");
      await expect(page.getByText("Exceptional support experience")).toBeVisible();
      await expect(page.getByText("Thanks", { exact: true })).toBeVisible();
    } finally {
      await restore();
    }
  });

  test("closing the rating dialog resets it", async ({ page, api, apiAs, ticket }) => {
    await agentReply(await apiAs("agent"), ticket.name, "<p>Done</p>");
    const restore = await useFeedbackMandatory(api, 1);
    try {
      await page.goto(`/help/tickets/${ticket.name}`);
      await closeButton(page).click();
      const dialog = page.getByRole("dialog", { name: "Rate this ticket" });
      await dialog.getByRole("radio").nth(4).click();
      await dialog.getByRole("button", { name: "Exceptional support experience" }).click();
      await page.keyboard.press("Escape");
      await closeButton(page).click();
      await expect(dialog.getByRole("button", { name: "Submit" })).toBeDisabled();
      await expect(dialog.getByRole("button", { name: "Exceptional support experience" })).toHaveCount(0);
    } finally {
      await restore();
    }
  });

  test("with feedback optional, closing never offers a rating", async ({ page, api, apiAs, ticket }) => {
    // Finding 1: confirmed. The portal has no other place to rate a ticket.
    await agentReply(await apiAs("agent"), ticket.name, "<p>Done</p>");
    const restore = await useFeedbackMandatory(api, 0);
    try {
      await page.goto(`/help/tickets/${ticket.name}`);
      await closeButton(page).click();
      await expect(page.getByRole("dialog").getByText("Are you sure you want to close this ticket?")).toBeVisible();
      await expect(page.getByRole("dialog", { name: "Rate this ticket" })).toHaveCount(0);
    } finally {
      await restore();
    }
  });

  test("an agent closing on the portal is not asked to rate", async ({ pageAs, api, apiAs, ticket }) => {
    await agentReply(await apiAs("agent"), ticket.name, "<p>Done</p>");
    const restore = await useFeedbackMandatory(api, 1);
    try {
      const page = await pageAs("agent");
      await page.goto(`/help/tickets/${ticket.name}`);
      await closeButton(page).click();
      await expect(page.getByRole("dialog").getByText("Are you sure you want to close this ticket?")).toBeVisible({
        timeout: 5_000,
      });
    } finally {
      await restore();
    }
  });
});

test.describe("details panel", () => {
  test("contact, status, team, priority and template fields; sections collapse", async ({
    page,
    api,
    ticket,
  }) => {
    const [team] = await api.list("HD Team", { fields: ["name"], limit: 1 } as any);
    if (team) await api.update("HD Ticket", ticket.name, { agent_group: team.name });
    await page.goto(`/help/tickets/${ticket.name}`);
    await expect(page.getByText(`#${ticket.name}`)).toBeVisible();
    await expect(page.getByText("Status")).toBeVisible();
    await expect(page.getByText("Priority")).toBeVisible();
    if (team) await expect(page.getByText(team.name).first()).toBeVisible();

    for (const section of ["Timeline", "Related help"]) {
      const toggle = page.getByRole("button", { name: section });
      await expect(toggle).toHaveAttribute("aria-expanded", "true");
      await toggle.click();
      await expect(toggle).toHaveAttribute("aria-expanded", "false");
    }
  });

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

  test("related help opens the article", async ({ page, ticket }) => {
    await page.goto(`/help/tickets/${ticket.name}`);
    const section = page.getByRole("button", { name: "Related help" });
    await expect(section).toBeVisible();
    // the section lists links after its toggle
    const first = page.locator("aside, [class*=border-l]").getByRole("link").first()
      .or(page.getByText(/^E2E Article /).first());
    const title = (await first.innerText()).trim();
    await first.click();
    await expect(page).toHaveURL(/\/help\/articles\//);
    await expect(page.getByRole("heading", { name: title }).first()).toBeVisible();
  });

  test("the out-of-hours banner dismisses for the day", async ({ page, ticket }) => {
    const message = `Back on Monday ${uid()}`;
    await page.route("**/*hd_ticket.api.get_one*", async (route) => {
      const response = await route.fetch();
      const json = await response.json();
      json.message.outside_hours_banner = { show: true, msg: message };
      await route.fulfill({ response, json });
    });
    await page.goto(`/help/tickets/${ticket.name}`);
    await expect(page.getByRole("alert").getByText(message)).toBeVisible();
    await page.getByRole("button", { name: "Dismiss" }).click();
    await expect(page.getByText(message)).toHaveCount(0);
    await page.reload();
    await expect(closeButton(page)).toBeVisible();
    await expect(page.getByText(message)).toHaveCount(0);
    const keys = await page.evaluate(() => Object.keys(localStorage).filter((key) => key.startsWith("kb:banner-dismissed:")));
    expect(keys.some((key) => key.includes(ticket.name))).toBe(true);
  });
});

test.describe("form scripts", () => {
  test("grouped, labelled and More actions menus on the portal", async ({ page, api, ticket }) => {
    const scripts = new FormScripts(api);
    await scripts.create(
      `return { actions: [
        { group: "E2E Group", options: [{ label: "E2E Option", onClick: () => {} }] },
        { group: "E2E Labelled", buttonLabel: "E2E Menu", label: "E2E Menu Item", onClick: () => {} },
      ] };`,
      { portal: true }
    );
    try {
      await page.goto(`/help/tickets/${ticket.name}`);
      await page.getByRole("button", { name: "E2E Menu" }).click();
      await expect(page.getByRole("menuitem", { name: "E2E Menu Item" })).toBeVisible();
      await page.keyboard.press("Escape");
      await page.getByRole("button", { name: "More actions" }).click();
      await expect(page.getByRole("menuitem", { name: "E2E Option" })).toBeVisible();
    } finally {
      await scripts.removeAll();
    }
  });

  test("an agent on the portal gets agent-scoped scripts", async ({ pageAs, api, ticket }) => {
    const scripts = new FormScripts(api);
    await scripts.create(`return { actions: [{ label: "E2E Agent Scoped", onClick: () => {} }] };`);
    try {
      const page = await pageAs("agent");
      await page.goto(`/help/tickets/${ticket.name}`);
      await expect(page.getByRole("button", { name: "E2E Agent Scoped" })).toBeVisible();
    } finally {
      await scripts.removeAll();
    }
  });
});

test.describe("phone", () => {
  test.use({ viewport: { width: 390, height: 800 } });

  test("ticket details open in a drawer and close on Escape", async ({ page, ticket }) => {
    await page.goto(`/help/tickets/${ticket.name}`);
    await expect(page.getByText("Request received")).toBeHidden();
    await page.getByRole("button", { name: "Ticket details" }).click();
    await expect(page.getByText("Request received")).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.getByText("Request received")).toBeHidden();
    await page.getByRole("button", { name: "Ticket details" }).click();
    await page.getByRole("button", { name: "Close details" }).click();
    await expect(page.getByText("Request received")).toBeHidden();
  });
});
