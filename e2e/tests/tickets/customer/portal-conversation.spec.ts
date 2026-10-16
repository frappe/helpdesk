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

  await page.goto(`/help/tickets/${ticket.name}`);
  await expectInConversation(page, agentReply);
  // closed on arrival; its bar opens it with the cursor in it
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
