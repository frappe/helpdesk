// Usability task test, workflow B: close and rate a resolved ticket, using the
// keyboard only. Checks that focus reaches the required fields (rating, reason)
// and the Submit button in the expected order, and that the keyboard submits.
import { customerDetails, expect, test } from "../support/app.mjs";

/** A short description of the element that has keyboard focus. */
async function focused(page) {
  return page.evaluate(() => {
    const element = document.activeElement;
    const label =
      element.getAttribute("aria-label") ||
      element.getAttribute("placeholder") ||
      (element.innerText || "").trim();
    return `${element.getAttribute("role") || element.tagName.toLowerCase()}: ${label}`;
  });
}

/** Press Tab until `pattern` has focus; return every stop passed on the way. */
async function tabTo(page, pattern, limit = 12) {
  const stops = [];
  for (let i = 0; i < limit; i++) {
    await page.keyboard.press("Tab");
    stops.push(await focused(page));
    if (pattern.test(stops.at(-1))) return stops;
  }
  throw new Error(`focus never reached ${pattern}; stops were: ${stops.join(" | ")}`);
}

test("task B: the rating form can be completed and submitted with the keyboard alone", async ({ app }) => {
  const name = await app.resolvedTicketWithReply(app.subject("Usability task B"));
  const page = await app.pageAs("customerA");

  // open the task screen
  await page.goto(`/helpdesk/my-tickets/${name}`);
  await expect(customerDetails(page)).toContainText(/Status\s*Resolved/);
  await page.getByRole("button", { name: "Close", exact: true }).focus();
  await page.keyboard.press("Enter");
  const dialog = page.getByRole("dialog", { name: "Rate this ticket" });
  await expect(dialog).toBeVisible();
  const order = [];

  // required field 1: the rating
  order.push(...(await tabTo(page, /^radio: 1 of 5$/)));
  await page.keyboard.press("ArrowRight");
  await page.keyboard.press("ArrowRight");
  await page.keyboard.press("ArrowRight");
  await expect(dialog.getByRole("radio", { name: "4 of 5" })).toBeFocused();
  await page.keyboard.press("Space");
  await expect(dialog.getByRole("radio", { name: "4 of 5" })).toBeChecked();

  // required field 2: the reason, which appears once a rating is chosen
  order.push(...(await tabTo(page, /Prompt, informative support$/)));
  await page.keyboard.press("Enter");

  // the optional comment, then the submit button, which is only now enabled
  order.push(...(await tabTo(page, /Tell us more$/)));
  await page.keyboard.type("Sorted quickly.");
  order.push(...(await tabTo(page, /^button: Submit$/)));
  await expect(dialog.getByRole("button", { name: "Submit" })).toBeFocused();

  // focus reached rating -> reason -> comment -> submit, in that order
  const position = (pattern) => order.findIndex((stop) => pattern.test(stop));
  const rating = position(/^radio: 1 of 5$/);
  const reason = position(/Prompt, informative support$/);
  const comment = position(/Tell us more$/);
  const submit = position(/^button: Submit$/);
  expect(rating, `focus order: ${order.join(" | ")}`).toBeGreaterThanOrEqual(0);
  expect(reason).toBeGreaterThan(rating);
  expect(comment).toBeGreaterThan(reason);
  expect(submit).toBeGreaterThan(comment);

  // the keyboard submits the form
  await page.keyboard.press("Enter");

  // the expected confirmation
  await expect(dialog).toBeHidden();
  await expect(customerDetails(page)).toContainText(/Status\s*Closed/);
  await expect(customerDetails(page)).toContainText("Prompt, informative support");

  const stored = await app.stored(name);
  expect(stored.status).toBe("Closed");
  expect(stored.feedback).toBe("Prompt, informative support");
  expect(stored.feedback_rating).toBe(0.8);
  expect(stored.feedback_extra).toBe("Sorted quickly.");
});
