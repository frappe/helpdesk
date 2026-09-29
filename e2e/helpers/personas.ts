import type { Api } from "./api";

export const PASSWORD = "E2e-Helpdesk-2026!";
export const CUSTOMER_ORG = "E2E Customer Org";

export type PersonaKey =
  | "admin"
  | "manager"
  | "agent"
  | "agent2"
  | "customer"
  | "customerManager";

export interface Persona {
  email: string;
  firstName: string;
  roles: string[];
  kind: "agent" | "customer";
}

export const personas: Record<Exclude<PersonaKey, "admin">, Persona> = {
  manager: agent("manager", "Mona", ["Agent", "Agent Manager"]),
  agent: agent("agent", "Arjun", ["Agent"]),
  agent2: agent("agent2", "Bela", ["Agent"]),
  customer: customer("customer", "Cora", ["HD Customer"]),
  customerManager: customer("customer-manager", "Dev", [
    "HD Customer",
    "HD Customer Manager",
  ]),
};

export function emailOf(key: PersonaKey) {
  return key === "admin" ? "Administrator" : personas[key].email;
}

export function storageStateOf(key: PersonaKey) {
  return `e2e/.auth/${key}.json`;
}

/** Idempotently create every persona with its roles, HD Agent or Contact. */
export async function seedPersonas(api: Api) {
  for (const persona of Object.values(personas)) {
    await ensureUser(api, persona);
    if (persona.kind === "agent") await ensureAgent(api, persona);
    else await ensureContact(api, persona);
  }
  await ensureCustomerOrg(api);
}

function agent(slug: string, firstName: string, roles: string[]): Persona {
  return { email: `e2e-${slug}@example.com`, firstName, roles, kind: "agent" };
}

function customer(slug: string, firstName: string, roles: string[]): Persona {
  return { email: `e2e-${slug}@example.com`, firstName, roles, kind: "customer" };
}

async function ensureUser(api: Api, persona: Persona) {
  const roles = persona.roles.map((role) => ({ role }));
  if (await api.exists("User", { name: persona.email })) {
    await api.update("User", persona.email, { roles, enabled: 1 });
    return;
  }
  await api.insert("User", {
    email: persona.email,
    first_name: persona.firstName,
    last_name: "E2E",
    send_welcome_email: 0,
    user_type: persona.kind === "agent" ? "System User" : "Website User",
    new_password: PASSWORD,
    roles,
  });
}

async function ensureAgent(api: Api, persona: Persona) {
  const name = await api.exists("HD Agent", { user: persona.email });
  if (name) return api.update("HD Agent", name, { is_active: 1 });
  await api.insert("HD Agent", {
    user: persona.email,
    agent_name: `${persona.firstName} E2E`,
    is_active: 1,
  });
}

async function ensureContact(api: Api, persona: Persona) {
  if (await api.exists("Contact", { email_id: persona.email })) return;
  await api.insert("Contact", {
    first_name: persona.firstName,
    last_name: "E2E",
    email_id: persona.email,
    user: persona.email,
    email_ids: [{ email_id: persona.email, is_primary: 1 }],
  });
}

async function ensureCustomerOrg(api: Api) {
  const contacts = await Promise.all(
    [personas.customer, personas.customerManager].map((persona) =>
      api.exists("Contact", { email_id: persona.email })
    )
  );
  const rows = contacts.map((contact_name, index) => ({
    contact_name,
    is_manager: index === 1 ? 1 : 0,
  }));
  if (await api.exists("HD Customer", { name: CUSTOMER_ORG })) {
    return api.update("HD Customer", CUSTOMER_ORG, { contacts: rows });
  }
  await api.insert("HD Customer", { customer_name: CUSTOMER_ORG, contacts: rows });
}
