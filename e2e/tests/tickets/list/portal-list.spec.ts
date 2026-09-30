import { expect, test, usePersona } from "../../../helpers/fixtures";
import { raiseTicket } from "../../../helpers/factories";

usePersona("customer");

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
