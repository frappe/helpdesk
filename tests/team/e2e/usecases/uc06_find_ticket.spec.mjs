// UC-06 Find a ticket in my list (actor: Customer, workflows A and B). Specification: ../USE_CASES.md
import { customerDetails, expect, test } from "../support/app.mjs";

const row = (page, name) => page.getByRole("link", { name: new RegExp(`^${name} `) });
const rows = (page) => page.getByRole("link", { name: /^\d+ / });

/** Open the list with no filter. The list remembers each user's last filter
 *  between visits, so a test must not rely on what an earlier visit left. */
async function openList(page) {
  await page.goto("/helpdesk/my-tickets");
  await page.waitForLoadState("networkidle");
  await page.getByRole("textbox", { name: "ID" }).fill("");
  await page.getByRole("textbox", { name: "Subject" }).fill("");
  await page.waitForLoadState("networkidle");
}

async function twoTickets(app, label) {
  const tag = Date.now().toString(36);
  const wanted = { subject: `${label} scanner ${tag}` };
  const other = { subject: `${label} keyboard ${tag}` };
  wanted.name = await app.newTicket(wanted.subject);
  other.name = await app.newTicket(other.subject);
  return { wanted, other, tag };
}

test.describe("UC-06 Find a ticket in my list", () => {
  test("MF: customer filters the list by subject and opens the ticket", async ({ app }) => {
    const { wanted, other } = await twoTickets(app, "UC06 MF");
    const before = await app.stored(wanted.name);
    const page = await app.pageAs("customerA");
    await openList(page);
    await expect(rows(page).first()).toBeVisible(); // the unfiltered list is paged; both tickets are in it

    await page.getByRole("textbox", { name: "Subject" }).fill(wanted.subject);

    // result shown
    await expect(row(page, other.name)).toHaveCount(0);
    await expect(rows(page)).toHaveCount(1);
    await expect(row(page, wanted.name)).toContainText("Open");
    await page.getByText(wanted.subject, { exact: true }).click();
    await expect(page).toHaveURL(new RegExp(`/helpdesk/my-tickets/${wanted.name}$`));
    await expect(customerDetails(page)).toContainText(wanted.subject);

    // postcondition: looking does not change the record
    expect((await app.stored(wanted.name)).modified).toBe(before.modified);
  });

  test("AF1: customer finds the ticket by its number", async ({ app }) => {
    const { wanted, other } = await twoTickets(app, "UC06 AF1");
    const page = await app.pageAs("customerA");
    await openList(page);

    await page.getByRole("textbox", { name: "ID" }).fill(String(wanted.name));

    await expect(rows(page)).toHaveCount(1);
    await expect(row(page, wanted.name)).toContainText(wanted.subject);
    await expect(row(page, other.name)).toHaveCount(0);
  });

  test("AF2: customer clears the default open-only filter to find a ticket an agent resolved", async ({ app }) => {
    const { wanted } = await twoTickets(app, "UC06 AF2");
    await app.setStatus(wanted.name, "Resolved"); // workflow B, by the agent, since the customer last looked
    const page = await app.pageAs("customerA");
    await openList(page);

    // the list opens with "Status is Open", which hides resolved and closed tickets
    await page.getByRole("button", { name: "Clear all Filter" }).click();
    await page.waitForLoadState("networkidle");
    await page.getByRole("textbox", { name: "ID" }).fill(String(wanted.name));

    await expect(row(page, wanted.name)).toContainText("Resolved");
    expect((await app.stored(wanted.name)).status).toBe("Resolved");
  });

  test("EF1: a filter that matches nothing shows an empty list", async ({ app }) => {
    const { wanted, tag } = await twoTickets(app, "UC06 EF1");
    const before = await app.stored(wanted.name);
    const page = await app.pageAs("customerA");
    await openList(page);
    await expect(rows(page).first()).toBeVisible();

    await page.getByRole("textbox", { name: "Subject" }).fill(`no-such-ticket-${tag}`);

    await expect(rows(page)).toHaveCount(0);
    await expect(page.getByText("No tickets found for the applied filters")).toBeVisible();
    expect((await app.stored(wanted.name)).modified).toBe(before.modified);
  });

  test("EF2: another customer's ticket never appears, even when filtered by its number", async ({ app }) => {
    const { wanted } = await twoTickets(app, "UC06 EF2");
    const page = await app.pageAs("customerB");
    await openList(page);
    await expect(row(page, wanted.name)).toHaveCount(0);

    await page.getByRole("textbox", { name: "ID" }).fill(String(wanted.name));

    await expect(rows(page)).toHaveCount(0);
    await expect(page.getByText(wanted.subject)).toHaveCount(0);
  });
});
