import type { Page, Route } from "@playwright/test";
import { expect, test, uid, usePersona } from "../support/fixtures";
import { raiseTicket } from "../support/factories";
import { personas } from "../support/personas";
import { createArticle, createCategory } from "../support/portal";

const PIXEL = "e2e/fixtures/pixel.png";

usePersona("customer");

test.describe("raising a ticket", () => {
  test("with a custom field and an inline image", async ({ page, api }) => {
    const template = await api.get("HD Ticket Template", "Default");
    await api.update("HD Ticket Template", "Default", {
      fields: [{ fieldname: "ticket_type", required: 0, hide_from_customer: 0 }],
    });
    try {
      const subject = `E2E portal ${uid()}`;
      await page.goto("/helpdesk/my-tickets/new");
      await page.getByRole("combobox", { name: "Select an option" }).click();
      await page.getByRole("option", { name: "Question" }).click();
      await page.getByPlaceholder("A short description").fill(subject);
      await page.locator(".ProseMirror").fill("Screenshot of the error");
      await attachImage(page);
      await page.getByRole("button", { name: "Submit" }).click();

      await expect(page).toHaveURL(/\/helpdesk\/my-tickets\/\d+$/);
      const [ticket] = await api.list("HD Ticket", {
        filters: { subject },
        fields: ["description", "ticket_type", "raised_by"],
      });
      expect(ticket.description).toContain("<img");
      expect(ticket.ticket_type).toBe("Question");
      expect(ticket.raised_by).toBe(personas.customer.email);
    } finally {
      await api.update("HD Ticket Template", "Default", { fields: template.fields });
    }
  });

  test("accepts a description that is only an image", async ({ page }) => {
    await page.goto("/helpdesk/my-tickets/new");
    await page.getByPlaceholder("A short description").fill(`E2E image only ${uid()}`);
    await attachImage(page);
    await expect(page.getByRole("button", { name: "Submit" })).toBeEnabled();
  });

  test("keeps Submit disabled while an image is uploading", async ({ page }) => {
    let release: () => void = () => {};
    const held = new Promise<void>((resolve) => (release = resolve));
    await page.route("**/api/method/upload_file", async (route: Route) => {
      await held;
      await route.continue();
    });

    await page.goto("/helpdesk/my-tickets/new");
    await page.getByPlaceholder("A short description").fill(`E2E upload ${uid()}`);
    await page.locator(".ProseMirror").fill("See the screenshot");
    const submit = page.getByRole("button", { name: "Submit" });
    await expect(submit).toBeEnabled();

    await chooseImage(page);
    await expect(submit).toBeDisabled();
    release();
    await expect(uploadedImage(page)).toBeVisible();
    await expect(submit).toBeEnabled();
  });

  test("suggests matching knowledge base articles", async ({ page, api, apiAs }) => {
    const probe = await (await apiAs("customer")).raw("helpdesk.api.article.search", { query: "probe" });
    test.skip(!probe.ok(), "article search needs RediSearch (redis-stack) on redis_cache");

    const category = await createCategory(api);
    const title = `Rotate ${uid()} credentials`;
    await createArticle(api, category.name, { title });
    await page.goto("/helpdesk/my-tickets/new");
    await page.getByPlaceholder("A short description").fill(title);
    await expect(page.getByText("These articles may already cover")).toBeVisible();
    await expect(page.getByText(title).last()).toBeVisible();
  });
});

test("lists only the customer's own tickets", async ({ page, apiAs }) => {
  const own = await raiseTicket(await apiAs("customer"));
  const colleague = await raiseTicket(await apiAs("customerManager"));

  await page.goto("/helpdesk/my-tickets");
  await expect(page.getByRole("link", { name: new RegExp(own.subject) })).toBeVisible();
  await expect(page.getByRole("link", { name: new RegExp(colleague.subject) })).toHaveCount(0);
});

test("customer manager sees every ticket of the organisation", async ({ pageAs, apiAs }) => {
  const colleague = await raiseTicket(await apiAs("customer"));
  const page = await pageAs("customerManager");

  await page.goto("/helpdesk/my-tickets");
  await expect(page.getByRole("link", { name: new RegExp(colleague.subject) })).toBeVisible();
});

test("conversation: customer and agent replies both show, internal comments never do", async ({
  page,
  apiAs,
  pageAs,
}) => {
  const ticket = await raiseTicket(await apiAs("customer"));
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

  await page.goto(`/helpdesk/my-tickets/${ticket.name}`);
  await expectInConversation(page, agentReply);
  await page.getByText("Type a message").click();
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
}) => {
  const ticket = await raiseTicket(await apiAs("customer"));
  await (await apiAs("agent")).call("run_doc_method", {
    dt: "HD Ticket",
    dn: ticket.name,
    method: "reply_via_agent",
    args: { message: "<p>Fixed on our side</p>" },
  });
  const mandatory = (await api.get("HD Settings", "HD Settings")).is_feedback_mandatory;
  await api.update("HD Settings", "HD Settings", { is_feedback_mandatory: 1 });
  try {
    await page.goto(`/helpdesk/my-tickets/${ticket.name}`);
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

test("public knowledge base: browse, rate an article, then raise a ticket from it", async ({
  page,
  api,
}) => {
  const category = await createCategory(api);
  const article = await createArticle(api, category.name);

  await page.goto("/helpdesk/kb-public");
  await page.getByText(category.category_name).click();
  await page.getByText(article.title, { exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`/kb-public/articles/${article.name}`));

  // ponytail: thumbs are bare clickable svgs; buttons with aria-labels would make this getByRole
  const thumbs = page
    .locator("div")
    .filter({ hasText: "Was this article Helpful?" })
    .filter({ has: page.locator("svg.cursor-pointer") })
    .last()
    .locator("svg.cursor-pointer");
  await thumbs.first().click();
  await expect(page.getByText("Feedback submitted successfully.")).toBeVisible();
  await expect
    .poll(async () => {
      const [row] = await api.list("HD Article Feedback", {
        filters: { article: article.name, user: personas.customer.email },
        fields: ["feedback"],
      });
      return row?.feedback;
    })
    .toBe("1");
  await page.getByRole("link", { name: "here" }).click();
  await expect(page).toHaveURL(/\/helpdesk\/my-tickets\/new/);
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

async function chooseImage(page: Page) {
  const chooser = page.waitForEvent("filechooser");
  await page.getByRole("button", { name: "Image / Gallery" }).click();
  await (await chooser).setFiles(PIXEL);
}

async function attachImage(page: Page) {
  await chooseImage(page);
  await expect(uploadedImage(page)).toBeVisible();
}

function uploadedImage(page: Page) {
  return page.locator('.ProseMirror img[src*="/files/"]');
}
