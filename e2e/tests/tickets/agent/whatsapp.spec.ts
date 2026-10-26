import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { Locator, Page } from "@playwright/test";
import type { Api } from "../../../helpers/api";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";
import { addComment, openTicket } from "../../../helpers/ticket";
import {
  approveTemplate,
  FakeMeta,
  makeWhatsAppAccount,
  newWhatsAppNumber,
  pressPromptButton,
  receiveWhatsApp,
  updateWhatsAppStatus,
  whatsAppMessagesOf,
} from "../../../helpers/whatsapp";

usePersona("agent");

const MESSAGES_API = "whatsapp.whatsapp.api.messages";
// big enough to show in the media screenshot
const PNG = readFileSync(join(process.cwd(), "desk/public/manifest/apple-icon-180.png"));
const SCREENS = process.env.SCREENS_DIR || join(process.cwd(), ".factory", "screens");
// PHONE=1 runs the whole spec on a touch phone against MobileTicketAgent
const PHONE = !!process.env.PHONE;
const TOUCH_PHONE = { viewport: { width: 390, height: 760 }, hasTouch: true, isMobile: true };
if (PHONE) test.use(TOUCH_PHONE);

const meta = new FakeMeta();
let metaUrl: string;

test.beforeAll(async () => {
  metaUrl = await meta.start();
});
test.afterAll(() => meta.stop());

type Seeded = { ticket: string; first: Record<string, any>; account: string; number: string };

async function seedTicket(api: Api, message = "Hi, my order has not arrived yet"): Promise<Seeded> {
  const account = await makeWhatsAppAccount(api, metaUrl);
  const number = newWhatsAppNumber();
  const first = await receiveWhatsApp(api, account, number, { message });
  return { ticket: first.reference_docname, first, account, number };
}

const thread = (page: Page) => page.getByTestId("whatsapp-thread");
// first match: a quote repeats the text of the message it quotes
const bubble = (page: Page, text: string) =>
  thread(page).getByRole("listitem").filter({ hasText: text }).first();
const direction = (message: Locator) => message.locator("[data-direction]");
const composer = (page: Page) => page.getByTestId("whatsapp-composer");
const composerBox = (page: Page) => composer(page).getByPlaceholder("Type a WhatsApp message");
// the bar's Reply has a visible label; a bubble's Reply is icon only
const replyButton = (page: Page) =>
  page.getByRole("button", { name: "Reply", exact: true }).filter({ hasText: "Reply" });

async function openWhatsApp(page: Page, ticket: string) {
  await openTicket(page, ticket, "#whatsapp");
  await expect(page.getByRole("tab", { name: "WhatsApp" })).toHaveAttribute("aria-selected", "true");
}

// the thread joins the ticket's room with doc_subscribe; the server checks permission before joining
function subscribedToTicket(page: Page, ticket: string): Promise<void> {
  return new Promise((resolve) =>
    page.on("websocket", (socket) =>
      socket.on("framesent", ({ payload }) => {
        const frame = String(payload);
        if (frame.includes("doc_subscribe") && frame.includes(ticket)) setTimeout(resolve, 1000);
      })
    )
  );
}

// a bubble's actions show on hover, and always on a touch phone
async function messageAction(page: Page, message: Locator, name: string) {
  const action = message.getByRole("button", { name, exact: true });
  if (await page.evaluate(() => matchMedia("(hover: none)").matches)) {
    await expect.poll(() => shownOpacity(action)).toBe(1);
    await action.tap();
  } else {
    await message.locator("[data-direction] > div").first().hover();
    await action.click();
  }
}

// Playwright counts opacity 0 as visible, so multiply it up the tree
function shownOpacity(control: Locator): Promise<number> {
  return control.evaluate((element) => {
    let opacity = 1;
    for (let node: Element | null = element; node; node = node.parentElement)
      opacity *= Number(getComputedStyle(node).opacity);
    return opacity;
  });
}

async function openComposer(page: Page) {
  await replyButton(page).click();
  await expect(composerBox(page)).toBeVisible();
  await composerSettled(page);
}

// the composer slides open over 250ms; layout checks and screenshots wait it out
async function composerSettled(page: Page) {
  await page.waitForFunction(() => !document.querySelector(".slide-enter-active"));
}

async function expectScrolledToLatest(page: Page) {
  await expect
    .poll(() => thread(page).evaluate((el) => el.scrollHeight - el.scrollTop - el.clientHeight))
    .toBeLessThan(8);
}

// a client side route change
async function navigateInApp(page: Page, path: string) {
  await page.evaluate(
    (to) => (document.querySelector("#app") as any).__vue_app__.config.globalProperties.$router.push(to),
    path
  );
}

// one shot per theme, so every scenario lands in the UI matrix
async function shoot(page: Page, scenario: string) {
  const device = (page.viewportSize()?.width ?? 1440) < 640 ? "phone" : "desktop";
  for (const theme of ["light", "dark"] as const) {
    await setTheme(page, theme);
    await page.screenshot({
      animations: "disabled",
      path: join(SCREENS, `agent-ui-${scenario}-${device}-${theme}.png`),
    });
  }
  await setTheme(page, "light");
}

async function setTheme(page: Page, theme: "light" | "dark") {
  await page.evaluate((value) => document.documentElement.setAttribute("data-theme", value), theme);
}

async function outgoing(api: Api, ticket: string) {
  const rows = await whatsAppMessagesOf(api, ticket, [
    "name",
    "direction",
    "message",
    "mime_type",
    "context_message_id",
    "reaction",
    "whatsapp_template",
    "creation",
  ]);
  return rows
    .filter((row) => row.direction === "Outgoing")
    .sort((a, b) => (a.creation < b.creation ? -1 : 1));
}

async function agentSends(apiAs: (key: "agent") => Promise<Api>, ticket: string, to: string, message: string) {
  return (await apiAs("agent")).call<string>(`${MESSAGES_API}.send_message`, {
    to,
    message,
    reference_doctype: "HD Ticket",
    reference_docname: ticket,
  });
}

test("the WhatsApp tab replaces Emails and shows the chat with delivery ticks", async ({
  page,
  api,
  apiAs,
}) => {
  const { ticket, first, account } = await seedTicket(api);
  const note = `Courier called ${uid()}`;
  await addComment(await apiAs("agent"), ticket, note);
  const read = await agentSends(apiAs, ticket, first.to, "We are checking with the courier");
  const failed = await agentSends(apiAs, ticket, first.to, "Could you share the *order number*?");
  await updateWhatsAppStatus(api, account, read, "read");
  await updateWhatsAppStatus(api, account, failed, "failed", [
    { code: 131047, title: "Re-engagement message", message: "Re-engagement message" },
  ]);

  await openTicket(page, ticket);
  await expect(page.getByRole("tab", { name: "Emails" })).toHaveCount(0);
  await page.getByRole("tab", { name: "Activity" }).click();
  const activity = page.getByRole("tabpanel", { name: "Activity" });
  await expect(activity.getByText(note)).toBeVisible();
  await expect(activity).not.toContainText("We are checking with the courier");
  await shoot(page, "activity");

  await page.getByRole("tab", { name: "WhatsApp" }).click();
  await expect(direction(bubble(page, "Hi, my order"))).toHaveAttribute("data-direction", "Incoming");
  await expect(direction(bubble(page, "courier"))).toHaveAttribute("data-direction", "Outgoing");
  await expect(bubble(page, "courier").locator(".lucide-check-check.text-ink-blue-5")).toBeVisible();
  const failedBubble = bubble(page, "order number");
  await expect(failedBubble).toContainText("Re-engagement message");
  await expect(failedBubble.locator("strong, b")).toHaveText("order number");
  await expect(failedBubble.getByRole("button", { name: "Reply", exact: true })).toHaveCount(0);
  await shoot(page, "thread");
  await shoot(page, "failed");
});

// a WhatsApp ticket opens on its chat, an explicit hash still wins, and an email ticket keeps its default
async function expectDefaultTabs(page: Page, api: Api, emailDefault: string) {
  const { ticket } = await seedTicket(api);
  await openTicket(page, ticket);
  await expect(page.getByRole("tab").first()).toHaveText("WhatsApp");
  await expect(selectedTab(page)).toHaveText("WhatsApp");
  expect(new URL(page.url()).hash).toBe("");
  await expect(bubble(page, "Hi, my order")).toBeVisible();

  await page.getByRole("tab", { name: "Activity" }).click();
  await expect(page).toHaveURL(/#activity$/);
  await page.reload();
  await expect(selectedTab(page)).toHaveText("Activity");

  const email = await api.insert("HD Ticket", { subject: `Email ${uid()}`, description: "x" });
  await openTicket(page, email.name);
  await expect(selectedTab(page)).toHaveText(emailDefault);
  await expect(page.getByRole("tab", { name: "WhatsApp" })).toHaveCount(0);
}

const selectedTab = (page: Page) => page.locator('[role="tab"][aria-selected="true"]');

test("a WhatsApp ticket opens on the WhatsApp tab, an email ticket on Activity", async ({ page, api }) => {
  await expectDefaultTabs(page, api, PHONE ? "Details" : "Activity");
});

test("the closed-ticket prompt and the customer's answer show in the thread", async ({ page, api }) => {
  const { ticket, account, number } = await seedTicket(api, "Where is my refund?");
  await api.update("HD Ticket", ticket, { status: "Closed" });
  await receiveWhatsApp(api, account, number, { message: "Hello again" });
  await pressPromptButton(api, account, number, ticket, "helpdesk_no_ticket");

  await openWhatsApp(page, ticket);
  const prompt = bubble(page, "is closed");
  await expect(direction(prompt)).toHaveAttribute("data-direction", "Outgoing");
  await expect(direction(bubble(page, "No, thanks"))).toHaveAttribute("data-direction", "Incoming");
  await expect(bubble(page, "won't open a new ticket")).toBeVisible();
  await shoot(page, "interactive-prompt");
});

test("an agent quotes a message, replies and reacts", async ({ page, api }) => {
  const { ticket, first } = await seedTicket(api, "Is the parcel insured?");
  await openWhatsApp(page, ticket);

  await messageAction(page, bubble(page, "insured"), "Reply");
  await expect(composer(page)).toContainText("Replying to");
  await expect(composer(page)).toContainText("Is the parcel insured?");
  await composerBox(page).fill("Yes, up to the full value");
  await composerSettled(page);
  await shoot(page, "quoted-reply-composer");
  await composerBox(page).press("Enter");

  const reply = bubble(page, "full value");
  await expect(reply).toContainText("Replying to");
  await expect(reply).toContainText("Is the parcel insured?");
  await expect(composerBox(page)).toHaveValue("");
  expect(await outgoing(api, ticket)).toEqual([
    expect.objectContaining({ message: "Yes, up to the full value", context_message_id: first.message_id }),
  ]);
  expect(meta.sent.at(-1)).toMatchObject({ context: { message_id: first.message_id } });
  await shoot(page, "quoted-reply");

  await messageAction(page, bubble(page, "insured"), "React");
  await page.getByRole("button", { name: "React with 👍" }).click();
  await expect(bubble(page, "insured").locator("[data-slot=reactions]")).toHaveText("👍");
  await expect
    .poll(async () => (await outgoing(api, ticket)).filter((row) => row.reaction))
    .toEqual([expect.objectContaining({ reaction: "👍", context_message_id: first.message_id })]);
  await shoot(page, "reaction");
});

test("an agent sends an image with a caption, and it shows in the thread", async ({ page, api }) => {
  const { ticket } = await seedTicket(api, "Here is the damage");
  await openWhatsApp(page, ticket);
  await openComposer(page);

  await composer(page).getByRole("button", { name: "Attach a file" }).click();
  const chooser = page.waitForEvent("filechooser");
  await page.getByRole("menuitem", { name: "Upload Image" }).click();
  await (await chooser).setFiles({
    name: `reply-${uid()}.png`,
    mimeType: "image/png",
    buffer: Buffer.concat([PNG, Buffer.from(uid())]),
  });
  const preview = page.getByRole("dialog");
  await preview.getByPlaceholder("Add a caption...").fill("Photo of the replacement");
  await preview.getByRole("button", { name: /send/i }).click();
  await expect
    .poll(async () => (await outgoing(api, ticket)).map((row) => row.mime_type))
    .toEqual(["image/png"]);
  const sent = bubble(page, "Photo of the replacement");
  await expect(sent.locator("img")).toBeVisible();
  await composerSettled(page);
  await shoot(page, "media");

  // a dismissed preview drops its image, so the next text goes alone
  await composer(page).getByRole("button", { name: "Attach a file" }).click();
  const again = page.waitForEvent("filechooser");
  await page.getByRole("menuitem", { name: "Upload Image" }).click();
  await (await again).setFiles({
    name: `abandoned-${uid()}.png`,
    mimeType: "image/png",
    buffer: Buffer.concat([PNG, Buffer.from(uid())]),
  });
  await expect(preview.getByPlaceholder("Add a caption...")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(preview).toBeHidden();
  await composerBox(page).fill("Just text now");
  await composerBox(page).press("Enter");
  await expect
    .poll(async () => (await outgoing(api, ticket)).map((row) => [row.message, row.mime_type || null]))
    .toEqual([
      ["Photo of the replacement", "image/png"],
      ["Just text now", null],
    ]);
});

test("a failed send shows one error toast", async ({ page, api }) => {
  const { ticket } = await seedTicket(api);
  await page.route(`**/api/method/${MESSAGES_API}.send_message`, (route) =>
    route.fulfill({
      status: 417,
      contentType: "application/json",
      body: JSON.stringify({
        exc_type: "ValidationError",
        _server_messages: JSON.stringify([JSON.stringify({ message: "Boom failure" })]),
      }),
    })
  );
  await openWhatsApp(page, ticket);
  await openComposer(page);
  await composerBox(page).fill("This will fail");
  await composerBox(page).press("Enter");
  await expect(page.getByText("Boom failure").first()).toBeVisible();
  // a one-off count: a retrying assertion would wait for the toasts to expire
  await page.waitForTimeout(300);
  expect(await page.getByText("Boom failure").count()).toBe(1);
  await expect(composerBox(page)).toHaveValue("This will fail");
});

test("saved replies insert WhatsApp text and templates send from the picker", async ({
  page,
  api,
  apiAs,
}) => {
  const { ticket, account } = await seedTicket(api);
  const title = `Courier delay ${uid()}`;
  await (await apiAs("agent")).insert("HD Saved Reply", {
    title,
    scope: "Personal",
    message: "<p><strong>Sorry</strong> for the wait, the courier is <em>on it</em>.</p>",
    actions: JSON.stringify([{ action_type: "Set Priority", value: "Urgent" }]),
  });
  const label = `E2E follow up ${uid()}`;
  const template = await insertTemplate(api, account, label);
  await insertTemplate(api, await makeWhatsAppAccount(api, metaUrl), `${label} other number`);

  await openWhatsApp(page, ticket);
  await openComposer(page);
  await composer(page).getByRole("button", { name: "Saved replies" }).click();
  await page.getByRole("dialog").getByText(title).click();
  await expect(composerBox(page)).toHaveValue("*Sorry* for the wait, the courier is _on it_.");
  await expect(composer(page)).toContainText(title);
  await composerBox(page).press("Enter");
  await expect.poll(async () => (await api.get("HD Ticket", ticket)).priority).toBe("Urgent");
  await expect(composerBox(page)).toHaveValue("");

  await composer(page).getByRole("button", { name: "Templates" }).click();
  const modal = page.getByRole("dialog", { name: "WhatsApp Templates" });
  await modal.getByRole("textbox", { name: "Search templates" }).fill(label);
  const card = modal.getByRole("button", { name: new RegExp(label) });
  await expect(card).toHaveCount(1);
  await expect(card).toContainText("following up on your ticket");
  await expect(card).toContainText("Helpdesk team");
  await card.click();
  await shoot(page, "template-picker");
  await modal.getByRole("button", { name: "Send", exact: true }).click();
  await expect(modal).toBeHidden();
  await expect
    .poll(async () => (await outgoing(api, ticket)).map((row) => row.whatsapp_template).filter(Boolean))
    .toEqual([template]);
});

// approved straight away: Meta's review is what FakeMeta skips
async function insertTemplate(api: Api, account: string, label: string): Promise<string> {
  const template = await api.insert("WA Template", {
    template_label: label,
    template_type: "Utility",
    language: "en",
    message: "Hello, we are following up on your ticket.",
    footer: "Helpdesk team",
    reference_doctype: "HD Ticket",
    whatsapp_account: account,
  });
  await approveTemplate(api, template.name);
  return template.name;
}

test("the command palette inserts a saved reply into the WhatsApp composer", async ({
  page,
  api,
  apiAs,
}) => {
  test.skip(PHONE, "the phone layout has no command palette");
  const { ticket } = await seedTicket(api);
  const title = `Palette reply ${uid()}`;
  await (await apiAs("agent")).insert("HD Saved Reply", {
    title,
    scope: "Personal",
    message: "<p>Thanks for <strong>waiting</strong></p>",
  });
  await openWhatsApp(page, ticket);
  // Desktop Chrome's user agent is Windows, where Mod is Control
  await page.keyboard.press("Control+k");
  const search = page.getByRole("combobox", { name: /Search commands/ });
  await search.fill("Saved Replies");
  await page.getByRole("option", { name: /^Saved Replies/ }).click();
  await search.fill(title);
  await page.getByRole("option", { name: new RegExp(title) }).first().click();
  await expect(composerBox(page)).toHaveValue("Thanks for *waiting*");
  await expect(page.getByText("Could not open the reply box")).toHaveCount(0);
});

test("after the reply window closes only a template can be sent", async ({ page, api }) => {
  const { ticket } = await seedTicket(api);
  await page.clock.setFixedTime(Date.now() + 25 * 60 * 60 * 1000);
  await openWhatsApp(page, ticket);
  await replyButton(page).click();

  const templateOnly = composer(page).getByTestId("whatsapp-template-only");
  await expect(templateOnly).toContainText("The 24-hour reply window has closed.");
  await expect(composerBox(page)).toHaveCount(0);
  await composerSettled(page);
  await shoot(page, "template-only");
  await templateOnly.getByRole("button", { name: "Send Template" }).click();
  await expect(page.getByRole("dialog", { name: "WhatsApp Templates" })).toBeVisible();
});

test("a ticket with no messages shows the empty state, a slow load a spinner and a failed one a retry", async ({
  page,
  api,
}) => {
  const empty = await api.insert("HD Ticket", { subject: `Empty WhatsApp ${uid()}`, source: "WhatsApp" });
  await openWhatsApp(page, empty.name);
  await expect(thread(page)).toContainText("No WhatsApp messages yet");
  await shoot(page, "empty");
  await replyButton(page).click();
  await expect(composer(page).getByTestId("whatsapp-no-recipient")).toHaveText(
    "This contact has not messaged on WhatsApp yet"
  );
  await expect(composer(page).getByRole("button", { name: /Send Template|Templates/ })).toHaveCount(0);
  await expect(composerBox(page)).toHaveCount(0);
  await composerSettled(page);
  await shoot(page, "no-recipient");

  const { ticket } = await seedTicket(api, "Retry me");
  let release = () => {};
  const held = new Promise<void>((resolve) => (release = resolve));
  await page.route(`**/api/method/${MESSAGES_API}.get_messages`, async (route) => {
    await held;
    await route.continue();
  });
  await openTicket(page, ticket);
  await expect(thread(page).getByRole("status", { name: "Loading" })).toBeVisible();
  await shoot(page, "loading");
  release();
  await expect(bubble(page, "Retry me")).toBeVisible();
  await page.unroute(`**/api/method/${MESSAGES_API}.get_messages`);

  let failures = 1;
  await page.route(`**/api/method/${MESSAGES_API}.get_messages`, (route) =>
    failures-- > 0 ? route.fulfill({ status: 500, body: "{}" }) : route.continue()
  );
  await page.reload();
  await expect(thread(page)).toContainText("Could not load the WhatsApp conversation");
  await shoot(page, "error");
  await thread(page).getByRole("button", { name: "Retry" }).click();
  await expect(bubble(page, "Retry me")).toBeVisible();
});

test("a new customer message shows up without a reload", async ({ page, api }) => {
  const { ticket, account, number } = await seedTicket(api);
  const subscribed = subscribedToTicket(page, ticket);
  await openWhatsApp(page, ticket);
  await expect(bubble(page, "has not arrived")).toBeVisible();
  await subscribed;
  const text = `Still waiting ${uid()}`;
  await receiveWhatsApp(api, account, number, { message: text });
  await expect(bubble(page, text)).toBeVisible();

  await navigateInApp(page, "/tickets");
  await expect(thread(page)).toHaveCount(0);
  const whileAway = `Sent while away ${uid()}`;
  await receiveWhatsApp(api, account, number, { message: whileAway });
  await navigateInApp(page, `/tickets/${ticket}#whatsapp`);
  await expect(bubble(page, whileAway)).toBeVisible();
});

test("the latest message stays in view when replying to it", async ({ page, api }) => {
  const { ticket, account, number } = await seedTicket(api, "First of many");
  for (let index = 1; index <= 14; index++) {
    await receiveWhatsApp(api, account, number, { message: `Desktop note ${index}.` });
  }
  await openWhatsApp(page, ticket);
  const latest = bubble(page, "Desktop note 14.");
  await expect(latest).toBeInViewport();
  await messageAction(page, latest, "Reply");
  await expect(composerBox(page)).toBeVisible();
  await composerSettled(page);
  await expectScrolledToLatest(page);
  await expect(latest).toBeInViewport();
});

test.describe("on a touch phone", () => {
  test.use(TOUCH_PHONE);

  test("a WhatsApp ticket opens on the WhatsApp tab, an email ticket on Details", async ({ page, api }) => {
    await expectDefaultTabs(page, api, "Details");
  });

  test("the phone ticket page has the WhatsApp tab and composer", async ({ page, api }) => {
    const { ticket, account, number } = await seedTicket(api, "Sent from my phone");
    for (let index = 1; index <= 8; index++) {
      await receiveWhatsApp(api, account, number, { message: `Follow up number ${index}` });
    }
    const subscribed = subscribedToTicket(page, ticket);
    await openWhatsApp(page, ticket);
    await expect(page.getByRole("tab", { name: "Emails" })).toHaveCount(0);
    await expect(bubble(page, "Follow up number 8")).toBeInViewport();
    await subscribed;
    const live = `Arrived live ${uid()}`;
    await receiveWhatsApp(api, account, number, { message: live });
    await expect(bubble(page, live)).toBeInViewport();

    await messageAction(page, bubble(page, live), "Reply");
    await expect(composerBox(page)).toBeVisible();
    await composerSettled(page);
    await expectScrolledToLatest(page);
    await expect(bubble(page, live)).toBeInViewport();
    await composerBox(page).fill("Replying from the phone view");
    await shoot(page, "mobile-composer");
    await composer(page).getByRole("button", { name: "Send", exact: true }).tap();
    await expect
      .poll(async () => (await outgoing(api, ticket)).map((row) => row.message))
      .toEqual(["Replying from the phone view"]);
    await expect(composerBox(page)).toHaveValue("");

    // the phone page is reused across tickets, so a draft must not follow the agent
    await composerBox(page).fill("Draft meant for this ticket only");
    const next = await seedTicket(api, "A different customer");
    await navigateInApp(page, `/tickets/${next.ticket}#whatsapp`);
    await expect(bubble(page, "A different customer")).toBeVisible();
    await replyButton(page).click();
    await expect(composerBox(page)).toHaveValue("");
  });
});
