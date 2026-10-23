import { expect, test, uid } from "../../../helpers/fixtures";
import { expectDenied } from "../../../helpers/api";
import { PASSWORD, personas } from "../../../helpers/personas";
import { loginContext } from "../../../helpers/portal";
import { createThrowawayAgent } from "../../../helpers/settings";

const NEW_TICKET = "helpdesk.helpdesk.doctype.hd_ticket.api.new";
const RATE_LIMIT = 300;

function ticketDoc() {
  const subject = `E2E api ${uid()}`;
  return { subject, description: `<p>${subject}</p>` };
}

test("malformed attachments are refused instead of crashing", async ({ apiAs }) => {
  const customer = await apiAs("customer");

  for (const attachments of [[{}], [null], ["abc"], [{ file_url: "/files/x.png" }], [{ x: 1 }]]) {
    const response = await customer.raw(NEW_TICKET, { doc: ticketDoc(), attachments });
    expect(response.status(), JSON.stringify(attachments)).toBe(417);
  }
});

test("an image pasted twice leaves no upload of it orphaned", async ({ baseURL, api }) => {
  const customer = await loginContext(baseURL!, personas.customer.email, PASSWORD);
  // identical bytes share one URL; the first upload is an abandoned draft's
  const buffer = Buffer.from(`inline ${uid()}`);
  const uploads = [];
  for (let i = 0; i < 3; i++) {
    const response = await customer.post("/api/method/upload_file", {
      multipart: { file: { name: "inline.png", mimeType: "image/png", buffer }, is_private: "1" },
    });
    uploads.push((await response.json()).message);
  }
  expect(new Set(uploads.map((file) => file.file_url)).size).toBe(1);

  const img = `<img src="${uploads[0].file_url}">`;
  const response = await customer.post(`/api/method/${NEW_TICKET}`, {
    data: { doc: { ...ticketDoc(), description: `<p>${img}${img}</p>` } },
  });
  const ticket = (await response.json()).message;

  const files = await api.list("File", {
    filters: { name: ["in", uploads.map((file) => file.name)] },
    fields: ["attached_to_doctype", "attached_to_name"],
  });
  expect(files).toEqual(
    Array(3).fill({ attached_to_doctype: "HD Ticket", attached_to_name: String(ticket.name) })
  );
});

test("a flood of ticket creates from one user is rate limited", async ({ baseURL, api, apiAs }) => {
  const email = `e2e-flood-${uid()}@example.com`;
  await createThrowawayAgent(api, email, PASSWORD);
  const flooder = await loginContext(baseURL!, email, PASSWORD);

  // malformed, so the flood is counted without creating tickets
  const statuses = [];
  for (let i = 0; i < RATE_LIMIT + 5; i++) {
    const data = { doc: ticketDoc(), attachments: [{}] };
    statuses.push((await flooder.post(`/api/method/${NEW_TICKET}`, { data })).status());
  }

  expect(statuses.filter((status) => status === 429)).toHaveLength(5);
  // others keep their own budget
  await (await apiAs("customer")).call(NEW_TICKET, { doc: ticketDoc() });
});

test("a customer cannot rate a ticket while raising it", async ({ api, apiAs }) => {
  const doc = { ...ticketDoc(), feedback_rating: 1, feedback_extra: "great" };

  await expectDenied((await apiAs("customer")).raw(NEW_TICKET, { doc }));
  expect(await api.exists("HD Ticket", { subject: doc.subject })).toBeUndefined();
});

test("a customer's value for a read-only field is replaced by its default", async ({ api, apiAs }) => {
  // same field as portal-new.spec.ts
  if (!(await api.exists("Custom Field", { name: "HD Ticket-e2e_frozen" }))) {
    await api.insert("Custom Field", {
      dt: "HD Ticket",
      fieldname: "e2e_frozen",
      label: "E2E frozen",
      fieldtype: "Select",
      options: "No\nYes",
      default: "No",
      read_only: 1,
      insert_after: "description",
    });
  }

  const ticket = await (await apiAs("customer")).call(NEW_TICKET, {
    doc: { ...ticketDoc(), e2e_frozen: "Yes" },
  });

  expect((await api.get("HD Ticket", ticket.name)).e2e_frozen).toBe("No");
});
