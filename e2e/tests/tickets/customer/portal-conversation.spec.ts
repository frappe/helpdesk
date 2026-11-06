import type { Page } from "@playwright/test";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";

usePersona("customer");

test("conversation: customer and agent replies both show, internal comments never do", async ({
  page,
  apiAs,
  pageAs,
  ticket,
}) => {
  const agent = await apiAs("agent");
  const agentReply = `Agent answer ${uid()}`;
  const note = `Internal note ${uid()}`;
  const customerReply = `Customer follow up ${uid()}`;
  await agent.call("run_doc_method", {
    dt: "HD Ticket",
    dn: ticket.name,
    method: "reply_via_agent",
    args: { message: `<p>${agentReply}</p>` },
  });
  await agent.call("run_doc_method", {
    dt: "HD Ticket",
    dn: ticket.name,
    method: "new_comment",
    args: { content: `<p>${note}</p>` },
  });

  await page.goto(`/help/my-tickets/${ticket.name}`);
  await expectInConversation(page, agentReply);
  // closed on arrival; its bar opens it
  await page.getByText("Type a message").click();
  await expect(page.locator(".portal-reply-composer .ProseMirror")).toBeFocused();
  await page.locator(".ProseMirror").fill(customerReply);
  await page.getByRole("button", { name: "Send" }).click();
  await expectInConversation(page, customerReply);
  for (const frame of page.frames()) expect(await frame.content()).not.toContain(note);

  const agentPage = await pageAs("agent");
  await agentPage.goto(`/helpdesk/tickets/${ticket.name}`);
  await expectInConversation(agentPage, customerReply);
});

test("closing after an agent reply asks for a rating when feedback is mandatory", async ({
  page,
  api,
  apiAs,
  ticket,
}) => {
  await (await apiAs("agent")).call("run_doc_method", {
    dt: "HD Ticket",
    dn: ticket.name,
    method: "reply_via_agent",
    args: { message: "<p>Fixed on our side</p>" },
  });
  const mandatory = (await api.get("HD Settings", "HD Settings")).is_feedback_mandatory;
  await api.update("HD Settings", "HD Settings", { is_feedback_mandatory: 1 });
  try {
    await page.goto(`/help/my-tickets/${ticket.name}`);
    await page.getByRole("button", { name: "Close" }).click();
    const dialog = page.getByRole("dialog", { name: "Rate this ticket" });
    await dialog.getByRole("radio").nth(4).click();
    await dialog.getByRole("button", { name: "Exceptional support experience" }).click();
    await dialog.getByPlaceholder("Tell us more").fill("Quick turnaround");
    await dialog.getByRole("button", { name: "Submit" }).click();

    await expect
      .poll(async () => {
        const doc = await api.get("HD Ticket", ticket.name);
        return [doc.status, doc.feedback, doc.feedback_extra];
      })
      .toEqual(["Closed", "Exceptional support experience", "Quick turnaround"]);
    await expect(page.getByRole("button", { name: "Close" })).toHaveCount(0);
  } finally {
    await api.update("HD Settings", "HD Settings", { is_feedback_mandatory: mandatory });
  }
});

test("a ticket rated by email closes without asking for a rating again", async ({ page, api, apiAs, ticket }) => {
  await (await apiAs("agent")).call("run_doc_method", {
    dt: "HD Ticket",
    dn: ticket.name,
    method: "reply_via_agent",
    args: { message: "<p>Fixed on our side</p>" },
  });
  // Email feedback sets only the rating; the customer then wrote back and reopened it.
  await api.update("HD Ticket", ticket.name, { feedback_rating: 0.8, status: "Open" });
  const mandatory = (await api.get("HD Settings", "HD Settings")).is_feedback_mandatory;
  await api.update("HD Settings", "HD Settings", { is_feedback_mandatory: 1 });
  try {
    await page.goto(`/help/my-tickets/${ticket.name}`);
    await page.getByRole("button", { name: "Close" }).click();
    await expect(page.getByRole("dialog", { name: "Rate this ticket" })).toHaveCount(0);
    await page.getByRole("dialog", { name: "Close ticket" }).getByRole("button", { name: "Close ticket" }).click();
    await expect.poll(async () => (await api.get("HD Ticket", ticket.name)).status).toBe("Closed");
  } finally {
    await api.update("HD Settings", "HD Settings", { is_feedback_mandatory: mandatory });
  }
});

/** Email bodies render inside iframes, so wait until any frame shows the text. */
async function expectInConversation(page: Page, text: string) {
  await expect
    .poll(async () => {
      for (const frame of page.frames()) {
        if (await frame.getByText(text).count()) return true;
      }
      return false;
    })
    .toBe(true);
}
