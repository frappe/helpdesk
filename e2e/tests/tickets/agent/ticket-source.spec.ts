import type { Page } from "@playwright/test";
import type { Api } from "../../../helpers/api";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";
import { personas } from "../../../helpers/personas";
import { openTicket } from "../../../helpers/ticket";

usePersona("agent");

/** A ticket inserted by the Administrator, the way pulled emails arrive. */
async function emailTicket(api: Api) {
  const subject = `E2E email ticket ${uid()}`;
  return api.insert("HD Ticket", {
    subject,
    description: `<p>${subject}</p>`,
    raised_by: personas.customer.email,
  });
}

async function sourceRowOnPhone(page: Page, name: string) {
  await page.setViewportSize({ width: 390, height: 760 });
  await openTicket(page, name);
  await page.getByRole("tab", { name: "Details" }).click();
  return page.getByText("Source", { exact: true }).locator("..");
}

test("the contact card says which channel a ticket came in through", async ({
  page,
  api,
  ticket,
}) => {
  expect((await api.get("HD Ticket", ticket.name)).source).toBe("Portal");
  await openTicket(page, ticket.name);
  await expect(page.getByText("via Portal", { exact: true })).toBeVisible();

  const emailed = await emailTicket(api);
  expect(emailed.source).toBe("Email");
  await openTicket(page, emailed.name);
  await expect(page.getByText("via Email", { exact: true })).toBeVisible();
});

test("the phone details tab shows the ticket source", async ({ page, api, ticket }) => {
  await expect(await sourceRowOnPhone(page, ticket.name)).toContainText("Portal");

  const emailed = await emailTicket(api);
  await expect(await sourceRowOnPhone(page, emailed.name)).toContainText("Email");
});
