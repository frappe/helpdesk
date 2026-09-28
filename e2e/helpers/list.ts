import { expect, type Page } from "@playwright/test";
import type { Api } from "./api";

/** The agent ticket list at /helpdesk/tickets. */
export class TicketList {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto("/helpdesk/tickets");
    await expect(this.page.getByRole("button", { name: "Filter" })).toBeVisible();
  }

  rows() {
    return this.page.locator("#list-rows a");
  }

  row(subject: string) {
    return this.rows().filter({ hasText: subject });
  }

  /** Narrow the list to this spec's tickets through the Subject quick filter. */
  async searchSubject(text: string) {
    const reloaded = this.page.waitForResponse(/get_list_data/);
    await this.page.getByRole("textbox", { name: "Subject" }).fill(text);
    await reloaded;
  }

  async select(...subjects: string[]) {
    for (const subject of subjects) {
      await this.row(subject).getByRole("checkbox").check();
    }
  }

  /** The floating bar that appears once rows are selected. */
  selectionBar() {
    return this.page
      .getByText(/\d+ rows? selected/)
      .locator("xpath=ancestor::div[contains(@class, 'shadow-2xl')]");
  }

  async selectionMenu(item: string) {
    await this.selectionBar().locator("[aria-haspopup=menu]").click();
    await this.page.getByRole("menuitem", { name: item }).click();
  }

  /** Save the current filters as a new view and return its HD View name. */
  async createView(api: Api, label: string) {
    await this.page.getByRole("button", { name: "List", exact: true }).click();
    await this.page.getByRole("menuitem", { name: "Create View" }).click();
    const dialog = this.page.getByRole("dialog", { name: "Create View" });
    await dialog.getByRole("textbox").first().fill(label);
    await dialog.getByRole("button", { name: "Create" }).click();
    await expect(this.page).toHaveURL(/\?view=/);
    await expect.poll(() => api.exists("HD View", { label })).toBeTruthy();
    return (await api.exists("HD View", { label }))!;
  }

  /** Run an action from a view's kebab menu in the breadcrumb dropdown. */
  async viewAction(label: string, action: string) {
    await this.page.getByRole("banner").locator("button[aria-haspopup=menu]").first().click();
    const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    // standard views carry a "Standard" badge in their name
    const name = new RegExp(`^${escaped}( Standard)?$`);
    const item = this.page.getByRole("menuitem", { name });
    await item.hover();
    await item.getByRole("button").click();
    await this.page.getByRole("menuitem", { name: action }).click();
  }

  async addFilter(field: string, value: string) {
    await this.page.getByRole("button", { name: "Filter" }).click();
    const popover = this.page.getByRole("dialog", { name: "Filter" });
    await expect(popover).toBeVisible();
    const addFilter = popover.getByRole("button", { name: "Add filter" });
    if (await addFilter.isVisible()) await addFilter.click();
    await popover.getByRole("textbox").fill(field);
    await this.page.getByRole("option", { name: field, exact: true }).click();
    await this.page.getByRole("option", { name: value, exact: true }).click();
  }
}

/** Drop the auto saved default view and any view a spec left behind. */
export async function resetDefaultTicketView(api: Api, user: string) {
  const views = await api.list("HD View", {
    filters: { user, dt: "HD Ticket", is_default: 1 },
  });
  views.push(...(await api.list("HD View", { filters: { label: ["like", "E2E view %"] } })));
  for (const view of views) await api.delete("HD View", view.name);
}
