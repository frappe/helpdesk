import { expect, type Page } from "@playwright/test";
import type { Api } from "./api";

/** Open the agent ticket view and wait for the feed to render. */
export async function openTicket(page: Page, name: string, hash = "") {
  await page.goto(`/helpdesk/tickets/${name}${hash}`);
  await expect(page.getByRole("tab", { name: "Activity" })).toBeVisible();
}

/** The composer's editor; the last one on the page is the open reply or comment box. */
export function composer(page: Page) {
  return page.locator(".ProseMirror[contenteditable=true]").last();
}

/** Post a comment through the composer and wait for the server to store it. */
export async function postComment(page: Page, text: string) {
  await page.getByRole("button", { name: "Comment", exact: true }).click();
  await composer(page).click();
  await composer(page).pressSequentially(text);
  const saved = page.waitForResponse(
    (r) =>
      r.url().endsWith("/api/method/run_doc_method") &&
      (r.request().postData() || "").includes("new_comment")
  );
  await page.getByRole("button", { name: /^Comment \(/ }).click();
  await saved;
}

/** Record the POST bodies of every call to one whitelisted method. */
export function recordCalls(page: Page, method: string) {
  const bodies: string[] = [];
  page.on("request", (request) => {
    if (request.url().endsWith(`/api/method/${method}`)) {
      bodies.push(request.postData() || "");
    }
  });
  return bodies;
}

/** Run a whitelisted HD Ticket method as whoever `api` is logged in as. */
export function runTicketMethod(api: Api, ticket: string, method: string, args: object) {
  return api.call("run_doc_method", { dt: "HD Ticket", dn: ticket, method, args });
}

/** Comment on a ticket as the agent `api` is logged in as; returns the Comment name. */
export function addComment(api: Api, ticket: string, content: string) {
  return runTicketMethod(api, ticket, "new_comment", { content: `<p>${content}</p>` });
}

/** Flip an HD Settings field and hand back a function that restores it. */
export async function setHelpdeskSetting(api: Api, field: string, value: unknown) {
  const before = (await api.get("HD Settings", "HD Settings"))[field];
  await api.update("HD Settings", "HD Settings", { [field]: value });
  return () => api.update("HD Settings", "HD Settings", { [field]: before });
}

/** A team with members, so its assignment rule has someone to pick. */
export async function createTeam(api: Api, name: string, users: string[]) {
  return api.insert("HD Team", {
    team_name: name,
    users: users.map((user) => ({ user })),
  });
}

export function comments(api: Api, ticket: string) {
  return api.list("Comment", {
    fields: ["name", "content", "comment_email", "owner"],
    filters: { reference_doctype: "HD Ticket", reference_name: ticket, comment_type: "Comment" },
  });
}
