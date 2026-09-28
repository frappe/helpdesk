import type { Page } from "@playwright/test";
import type { Api } from "../../helpers/api";
import { expect, test, uid, usePersona } from "../../helpers/fixtures";
import { personas } from "../../helpers/personas";
import {
  composer,
  createTeam,
  openTicket,
  recordCalls,
  setHelpdeskSetting,
} from "../../helpers/ticket";

usePersona("agent");

test("sidebar fields save once per change and persist", async ({ page, api, ticket }) => {
  const team = `E2E Team ${uid()}`;
  await createTeam(api, team, [personas.agent.email]);
  const setValue = recordCalls(page, "frappe.client.set_value");
  await openTicket(page, ticket.name);

  const pick = async (placeholder: string, option: string) => {
    const field = page.getByRole("combobox", { name: placeholder });
    await field.click();
    await field.fill(option);
    await page.getByRole("option", { name: option, exact: true }).click();
  };
  await pick("Set Priority...", "High");
  await expect.poll(() => setValue.length).toBe(1);
  await pick("Set Ticket Type...", "Bug");
  await expect.poll(() => setValue.length).toBe(2);
  await pick("Set Team...", team);
  await expect.poll(() => setValue.length).toBe(3);

  // clearing is its own save; picking after it must not send a second one
  await page.getByRole("combobox", { name: "Set Priority..." }).hover();
  await page.locator('[data-slot=trigger]:has([placeholder="Set Priority..."]) [data-slot=clear]').click();
  await expect.poll(() => setValue.length).toBe(4);
  await pick("Set Priority...", "Low");
  await expect.poll(() => setValue.length).toBe(5);
  await page.waitForLoadState("networkidle");
  expect(setValue).toHaveLength(5);

  await page.reload();
  await expect(page.getByRole("combobox", { name: "Set Priority..." })).toHaveValue("Low");
  await expect(page.getByRole("combobox", { name: "Set Ticket Type..." })).toHaveValue("Bug");
  await expect(page.getByRole("combobox", { name: "Set Team..." })).toHaveValue(team);
  const saved = await api.get("HD Ticket", ticket.name);
  expect(saved).toMatchObject({ priority: "Low", ticket_type: "Bug", agent_group: team });
});

test.fixme("setting a team that has no members does not error", async ({ page, ticket }) => {
  // fresh sites ship Billing with an enabled, empty round robin rule: IndexError in get_user_round_robin
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await openTicket(page, ticket.name);
  const field = page.getByRole("combobox", { name: "Set Team..." });
  await field.click();
  await field.fill("Billing");
  await page.getByRole("option", { name: "Billing", exact: true }).click();
  await page.waitForLoadState("networkidle");
  expect(errors).toEqual([]);
});

test("tags can be created with a colour, added and removed", async ({ page, api, ticket }) => {
  const tag = `e2e-${uid()}`;
  const tagsOnTicket = async () =>
    ((await api.get("HD Ticket", ticket.name))._user_tags || "")
      .split(",")
      .filter(Boolean)
      .sort();
  // a customer's first ticket is auto-tagged; start untagged
  await api.call("helpdesk.api.tags.update_tags", {
    doctype: "HD Ticket",
    name: ticket.name,
    removed: await tagsOnTicket(),
  });
  await openTicket(page, ticket.name);

  await page.getByRole("button", { name: "+ Add" }).click();
  await page.getByPlaceholder("Search or create tags").fill(tag);
  await page.getByRole("option", { name: `Create "${tag}"` }).click();
  await page.getByRole("button", { name: "Green" }).click();
  await expect.poll(tagsOnTicket).toEqual([tag]);
  expect((await api.get("Tag", tag)).color).toBe("Green");

  await page.getByTitle(tag).click();
  await page.getByRole("option", { name: tag }).click();
  await page.keyboard.press("Escape");
  await expect.poll(tagsOnTicket).toEqual([]);
  await expect(page.getByTitle(tag)).toHaveCount(0);
});

test.fixme("tag activity reads '&', not '&amp;'", async ({ page, api, ticket }) => {
  // log_tag_activity joins with " & ", saving sanitises it to &amp; and the log row renders text
  await api.call("helpdesk.api.tags.update_tags", {
    doctype: "HD Ticket",
    name: ticket.name,
    added: [{ name: `e2e-${uid()}` }],
    removed: ["First Ticket"],
  });
  await openTicket(page, ticket.name);
  await expect(page.getByText(/added tag .* & removed tag/)).toBeVisible();
});

test("agents are assigned and unassigned from the sidebar", async ({ page, api, ticket }) => {
  const assignees = async () =>
    (
      await api.list("ToDo", {
        fields: ["allocated_to"],
        filters: { reference_type: "HD Ticket", reference_name: ticket.name, status: "Open" },
      })
    ).map((todo) => todo.allocated_to);
  await openTicket(page, ticket.name);

  await page.getByRole("button", { name: "Set Assignee..." }).click();
  await page.getByRole("button", { name: "Bela E2E" }).click();
  await page.keyboard.press("Escape");
  await expect.poll(assignees).toEqual([personas.agent2.email]);

  await page.locator("body").click();
  await page.keyboard.press("a");
  // the popover is portaled after the sidebar, whose trigger now shows Bela too
  await page.getByRole("button", { name: "Bela E2E" }).last().click();
  await page.keyboard.press("Escape");
  await expect.poll(assignees).toEqual([]);
  await expect(page.getByRole("button", { name: "Set Assignee..." })).toBeVisible();
});

test.describe("assign within team", () => {
  let restore: Array<() => Promise<unknown>> = [];
  test.beforeAll(async ({ api }) => {
    restore = [
      await setHelpdeskSetting(api, "restrict_tickets_by_agent_group", 1),
      await setHelpdeskSetting(api, "assign_within_team", 1),
    ];
  });
  test.afterAll(async () => {
    for (const undo of restore.reverse()) await undo();
  });

  test("only the ticket team's agents are offered", async ({ page, api, ticket }) => {
    const team = `E2E Team ${uid()}`;
    await createTeam(api, team, [personas.agent.email, personas.manager.email]);
    await api.update("HD Ticket", ticket.name, { agent_group: team });
    await openTicket(page, ticket.name);

    // the team's rule may already have auto-assigned someone, so open via the shortcut
    await page.locator("body").click();
    await page.keyboard.press("a");
    await expect(page.getByRole("button", { name: "Mona E2E" }).last()).toBeVisible();
    await expect(page.getByRole("button", { name: "Bela E2E" })).toHaveCount(0);
  });
});

test("status changes from the menu and the s shortcut, and the subject is renamed", async ({
  page,
  api,
  ticket,
}) => {
  const status = async () => (await api.get("HD Ticket", ticket.name)).status;
  await openTicket(page, ticket.name);
  const header = page.getByRole("banner");

  await header.getByRole("button", { name: "Open" }).click();
  await page.getByRole("menuitem", { name: "Replied" }).click();
  await expect.poll(status).toBe("Replied");
  await expect(header.getByRole("button", { name: "Replied" })).toBeVisible();

  await page.locator("body").click();
  await page.keyboard.press("s");
  await page.getByRole("menuitem", { name: "Resolved" }).click();
  await expect.poll(status).toBe("Resolved");

  const subject = `Renamed ${uid()}`;
  await header.getByRole("button", { name: ticket.subject }).click();
  const dialog = page.getByRole("dialog", { name: "Rename Subject" });
  await dialog.getByRole("textbox").fill(subject);
  await dialog.getByRole("button", { name: /^Rename/ }).click();
  await expect(header.getByRole("button", { name: subject })).toBeVisible();
  expect((await api.get("HD Ticket", ticket.name)).subject).toBe(subject);
});

/** A personal saved reply that stages field, team and tag actions. */
async function stagingReply(apiAs: (key: "agent") => Promise<Api>, tag: string) {
  return (await apiAs("agent")).insert("HD Saved Reply", {
    title: `Escalate ${uid()}`,
    message: "<p>Thanks for writing in</p>",
    scope: "Personal",
    actions: JSON.stringify([
      { action_type: "Set Priority", value: "High" },
      { action_type: "Set Ticket Type", value: "Question" },
      { action_type: "Set Team", value: "Product Experts" },
      { action_type: "Add Tag", value: tag },
    ]),
  });
}

async function applySavedReply(page: Page, title: string) {
  await page.getByRole("button", { name: "Reply", exact: true }).click();
  await page.locator("[data-slot=root]:has(input[type=file]) + *").first().click();
  await page.getByRole("dialog").getByText(title).click();
  await expect(composer(page)).toContainText("Thanks for writing in");
  await page.getByRole("button", { name: "Show actions" }).click();
}

test("saved reply chips can be repointed and apply after sending", async ({ page, api, apiAs, ticket }) => {
  const team = `E2E Team ${uid()}`;
  const tag = `e2e-${uid()}`;
  await createTeam(api, team, [personas.agent.email]);
  const reply = await stagingReply(apiAs, tag);
  await openTicket(page, ticket.name);
  await applySavedReply(page, reply.title);

  await page.getByRole("button", { name: /^Type / }).click();
  for (const name of ["Bug", "Incident", "Question"]) {
    await expect(page.getByRole("listbox").getByRole("option", { name })).toBeVisible();
  }
  await page.getByRole("listbox").getByRole("option", { name: "Bug" }).click();
  await expect(page.getByRole("button", { name: /^Type / })).toContainText("Bug");

  await page.getByRole("button", { name: /^Team / }).click();
  await page.getByRole("combobox", { name: "Select team" }).fill(team);
  await page.getByRole("listbox").getByRole("option", { name: team }).click();
  await expect(page.getByRole("button", { name: /^Team / })).toContainText(team);

  await page.getByRole("button", { name: /^Send/ }).click();
  await expect
    .poll(async () => {
      const saved = await api.get("HD Ticket", ticket.name);
      return [saved.priority, saved.ticket_type, saved.agent_group, saved._user_tags?.includes(tag)];
    })
    .toEqual(["High", "Bug", team, true]);
});

test.fixme("a repointed chip reopens with the full list", async ({ page, apiAs, ticket }) => {
  // the picker keeps the picked label as its search text, so only that option shows
  const reply = await stagingReply(apiAs, `e2e-${uid()}`);
  await openTicket(page, ticket.name);
  await applySavedReply(page, reply.title);

  await page.getByRole("button", { name: /^Type / }).click();
  await page.getByRole("listbox").getByRole("option", { name: "Bug" }).click();
  await page.getByRole("button", { name: /^Type / }).click();
  for (const name of ["Bug", "Incident", "Question"]) {
    await expect(page.getByRole("listbox").getByRole("option", { name })).toBeVisible();
  }
});
