import type { Api } from "../../../helpers/api";
import { raiseTicket } from "../../../helpers/factories";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";
import { TicketList, resetDefaultTicketView } from "../../../helpers/list";
import { personas } from "../../../helpers/personas";

usePersona("manager");

test.beforeEach(async ({ api }) => {
  await resetDefaultTicketView(api, personas.manager.email);
});

test.afterEach(async ({ api }) => {
  await resetDefaultTicketView(api, personas.manager.email);
});

const SUBJECTS = { a: "alpha", b: "bravo", c: "charlie" };
type Key = keyof typeof SUBJECTS;

interface Context {
  api: Api;
  list: TicketList;
  id: string;
  names: Record<Key, string>;
}

// One case per field type and operator: raise tickets a, b and c, set them up
// over REST, apply the filter in the popover and check which ones stay listed.
interface FilterCase {
  field: string;
  operator?: string;
  setup?: (context: Context) => Promise<void>;
  enter: (context: Context) => Promise<void>;
  shown: Key[];
  hidden: Key[];
}

const pick =
  (...labels: string[]) =>
  async ({ list }: Context) => {
    for (const label of labels) {
      await list.filterPopover().getByRole("option", { name: label, exact: true }).click();
    }
  };

const type =
  (text: (context: Context) => string) =>
  async (context: Context) => {
    await context.list
      .filterPopover()
      .getByPlaceholder(/^(Value|Comma separated values)$/)
      .fill(text(context));
  };

const stars = (count: number) => async ({ list }: Context) => {
  await list.filterPopover().getByRole("radio", { name: `${count} of 5` }).click();
};

const each = (values: Record<Key, unknown>, field: string) => async ({ api, names }: Context) => {
  for (const key of Object.keys(values) as Key[]) {
    await api.update("HD Ticket", names[key], { [field]: values[key] });
  }
};

const subject = (key: Key) => (context: Context) => `${context.id} ${SUBJECTS[key]}`;
const priorities = each({ a: "High", b: "Medium", c: "Low" }, "priority");
const daysAgo = (days: number) =>
  new Date(Date.now() - days * 86_400_000).toISOString().slice(0, 10);

const cases: FilterCase[] = [
  { field: "Subject", enter: type(subject("b")), shown: ["b"], hidden: ["a", "c"] },
  {
    field: "Subject",
    operator: "Not Like",
    enter: type(subject("b")),
    shown: ["a", "c"],
    hidden: ["b"],
  },
  {
    field: "Subject",
    operator: "Equals",
    enter: type(subject("c")),
    shown: ["c"],
    hidden: ["a", "b"],
  },
  {
    field: "Subject",
    operator: "In",
    enter: type((context) => `${subject("a")(context)}, ${subject("c")(context)}`),
    shown: ["a", "c"],
    hidden: ["b"],
  },
  {
    field: "Subject",
    operator: "Not In",
    enter: type((context) => `${subject("a")(context)}, ${subject("c")(context)}`),
    shown: ["b"],
    hidden: ["a", "c"],
  },
  { field: "Priority", setup: priorities, enter: pick("High"), shown: ["a"], hidden: ["b", "c"] },
  {
    field: "Priority",
    operator: "Not Equals",
    setup: priorities,
    enter: pick("High"),
    shown: ["b", "c"],
    hidden: ["a"],
  },
  {
    field: "Priority",
    operator: "In",
    setup: priorities,
    enter: pick("High", "Low"),
    shown: ["a", "c"],
    hidden: ["b"],
  },
  {
    field: "Priority",
    operator: "Like",
    setup: priorities,
    enter: type(() => "Hig"),
    shown: ["a"],
    hidden: ["b", "c"],
  },
  {
    field: "Team",
    operator: "Is",
    setup: setTeamOnA,
    enter: pick("Set"),
    shown: ["a"],
    hidden: ["b", "c"],
  },
  {
    field: "Team",
    operator: "Is",
    setup: setTeamOnA,
    enter: pick("Not Set"),
    shown: ["b", "c"],
    hidden: ["a"],
  },
  {
    field: "Via Customer Portal",
    setup: each({ a: 1, b: 0, c: 1 }, "via_customer_portal"),
    enter: pick("Yes"),
    shown: ["a", "c"],
    hidden: ["b"],
  },
  {
    field: "Via Customer Portal",
    setup: each({ a: 1, b: 0, c: 1 }, "via_customer_portal"),
    enter: pick("No"),
    shown: ["b"],
    hidden: ["a", "c"],
  },
  {
    field: "Opening Date",
    setup: each({ a: "2020-01-15", b: daysAgo(3), c: daysAgo(0) }, "opening_date"),
    enter: pick("Today"),
    shown: ["c"],
    hidden: ["a", "b"],
  },
  {
    field: "Opening Date",
    setup: each({ a: "2020-01-15", b: daysAgo(3), c: daysAgo(0) }, "opening_date"),
    enter: pick("Last 7 Days"),
    shown: ["b", "c"],
    hidden: ["a"],
  },
  {
    field: "Rating",
    setup: each({ a: 0.6, b: 1, c: 0 }, "feedback_rating"),
    enter: stars(3),
    shown: ["a"],
    hidden: ["b", "c"],
  },
  {
    field: "Rating",
    operator: "Greater Than",
    setup: each({ a: 0.6, b: 1, c: 0 }, "feedback_rating"),
    enter: stars(3),
    shown: ["b"],
    hidden: ["a", "c"],
  },
  {
    field: "Assigned to",
    setup: assignManagerToA,
    enter: pick("@me"),
    shown: ["a"],
    hidden: ["b", "c"],
  },
  {
    field: "Tags",
    operator: "Is",
    setup: tagB,
    enter: pick("Set"),
    shown: ["b"],
    hidden: ["a", "c"],
  },
];

for (const filterCase of cases) {
  const operator = filterCase.operator ?? "default operator";
  const shown = filterCase.shown.map((key) => SUBJECTS[key]).join(", ");
  test(`${filterCase.field} with ${operator} keeps ${shown}`, async ({ page, api, apiAs }) => {
    const id = uid();
    const customer = await apiAs("customer");
    const names = {} as Record<Key, string>;
    for (const key of Object.keys(SUBJECTS) as Key[]) {
      names[key] = String((await raiseTicket(customer, `${id} ${SUBJECTS[key]}`)).name);
    }
    const list = new TicketList(page);
    const context = { api, list, id, names };
    await filterCase.setup?.(context);

    await list.goto();
    await list.chooseFilterField(filterCase.field);
    if (filterCase.operator) await list.chooseFilterOperator(filterCase.operator);
    await filterCase.enter(context);

    // hidden first: it only passes once the filtered list has loaded
    for (const key of filterCase.hidden) {
      await expect(list.row(`${id} ${SUBJECTS[key]}`)).toHaveCount(0);
    }
    for (const key of filterCase.shown) {
      await expect(list.row(`${id} ${SUBJECTS[key]}`)).toBeVisible();
    }
  });
}

async function setTeamOnA({ api, id, names }: Context) {
  const team = await api.insert("HD Team", {
    team_name: `E2E Team ${id}`,
    users: [{ user: personas.manager.email }],
  });
  await api.update("HD Ticket", names.a, { agent_group: team.name });
}

async function assignManagerToA({ api, names }: Context) {
  await api.call("frappe.desk.form.assign_to.add", {
    doctype: "HD Ticket",
    name: names.a,
    assign_to: JSON.stringify([personas.manager.email]),
  });
}

async function tagB({ api, id, names }: Context) {
  await api.call("frappe.desk.doctype.tag.tag.add_tag", {
    tag: `e2e-${id}`,
    dt: "HD Ticket",
    dn: names.b,
  });
}
