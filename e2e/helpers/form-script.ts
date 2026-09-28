import type { Page } from "@playwright/test";
import type { Api } from "./api";
import { uid } from "./fixtures";

export const TEMPLATE = "E2E Form Script";

interface ScriptOptions {
  portal?: boolean;
  newPage?: boolean;
  enabled?: boolean;
}

/** Tracks the HD Form Scripts a spec creates so they can all be removed. */
export class FormScripts {
  private names: string[] = [];

  constructor(private api: Api) {}

  async create(body: string, options: ScriptOptions = {}) {
    const name = `E2E Script ${uid()}`;
    await this.api.insert("HD Form Script", {
      __newname: name,
      dt: "HD Ticket",
      apply_to: "Form",
      enabled: options.enabled === false ? 0 : 1,
      apply_to_customer_portal: options.portal ? 1 : 0,
      apply_on_new_page: options.newPage ? 1 : 0,
      script: `function setupForm(ctx) {\n${body}\n}`,
    });
    this.names.push(name);
    return name;
  }

  async removeAll() {
    for (const name of this.names.splice(0)) {
      await this.api.delete("HD Form Script", name);
    }
  }
}

/** A script that shows one button which counts its clicks on window. */
export function countingAction(label: string, extra = "") {
  return `return { actions: [{ label: "${label}", onClick: () => {
    window.__e2eClicks = (window.__e2eClicks || 0) + 1;
  } }${extra}] };`;
}

export function clicksOn(page: Page) {
  return page.evaluate(() => (window as any).__e2eClicks || 0);
}

const CUSTOM_FIELDS = [
  { fieldname: "e2e_trigger", fieldtype: "Select", options: "\nShow\nHide" },
  { fieldname: "e2e_choice", fieldtype: "Select", options: "Alpha\nBeta\nGamma" },
  { fieldname: "e2e_shown", fieldtype: "Data", depends_on: "eval:doc.e2e_trigger=='Show'" },
  {
    fieldname: "e2e_needed",
    fieldtype: "Data",
    mandatory_depends_on: "eval:doc.e2e_trigger=='Show'",
  },
  {
    fieldname: "e2e_locked",
    fieldtype: "Data",
    read_only_depends_on: "eval:doc.e2e_trigger=='Show'",
  },
];

/** A ticket template whose fields exercise onChange, filters and depends_on. */
export async function ensureTemplate(api: Api) {
  for (const field of CUSTOM_FIELDS) {
    const name = `HD Ticket-${field.fieldname}`;
    if (await api.exists("Custom Field", { name })) continue;
    await api.insert("Custom Field", {
      dt: "HD Ticket",
      label: field.fieldname.replace("e2e_", "E2E "),
      insert_after: "description",
      ...field,
    });
  }
  if (await api.exists("HD Ticket Template", { name: TEMPLATE })) return;
  await api.insert("HD Ticket Template", {
    template_name: TEMPLATE,
    fields: CUSTOM_FIELDS.map(({ fieldname }) => ({ fieldname })),
  });
}
