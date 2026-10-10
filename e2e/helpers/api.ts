import { expect, request, type APIRequestContext, type APIResponse } from "@playwright/test";
import { siteHeader } from "./site";

type Doc = Record<string, any>;

/**
 * Thin Frappe REST client bound to one logged-in user.
 * The session never renders a page, so Frappe issues it no CSRF token and
 * unsafe requests go through without one.
 */
export class Api {
  constructor(private context: APIRequestContext) {}

  static async login(baseURL: string, user: string, password: string) {
    const context = await request.newContext({
      baseURL,
      extraHTTPHeaders: siteHeader(),
    });
    const response = await context.post("/api/method/login", {
      form: { usr: user, pwd: password },
    });
    if (!response.ok()) throw new Error(`Login failed for ${user}`);
    return new Api(context);
  }

  async call<T = any>(method: string, args: Doc = {}): Promise<T> {
    const body = await this.send("post", `/api/method/${method}`, args);
    return body.message;
  }

  /** For whitelisted methods that only accept GET. */
  async callGet<T = any>(method: string, args: Record<string, string> = {}): Promise<T> {
    return (await this.send("get", `/api/method/${method}?${new URLSearchParams(args)}`)).message;
  }

  async get<T = Doc>(doctype: string, name: string): Promise<T> {
    return (await this.send("get", this.path(doctype, name))).data;
  }

  async insert<T = Doc>(doctype: string, doc: Doc): Promise<T> {
    return (await this.send("post", this.path(doctype), doc)).data;
  }

  async update<T = Doc>(doctype: string, name: string, doc: Doc): Promise<T> {
    return (await this.send("put", this.path(doctype, name), doc)).data;
  }

  async delete(doctype: string, name: string) {
    await this.send("delete", this.path(doctype, name));
  }

  async exists(doctype: string, filters: Doc): Promise<string | undefined> {
    const rows = await this.list(doctype, { filters, limit: 1 });
    return rows[0]?.name;
  }

  async list<T = Doc>(
    doctype: string,
    options: { fields?: string[]; filters?: Doc; limit?: number } = {}
  ): Promise<T[]> {
    const params = new URLSearchParams({
      fields: JSON.stringify(options.fields || ["name"]),
      filters: JSON.stringify(options.filters || {}),
      limit_page_length: String(options.limit || 0),
    });
    return (await this.send("get", `${this.path(doctype)}?${params}`)).data;
  }

  /** Raw request for tests that assert on failures (permission checks). */
  raw(method: string, args: Doc = {}) {
    return this.context.post(`/api/method/${method}`, { data: args });
  }

  private path(doctype: string, name?: string) {
    const base = `/api/resource/${encodeURIComponent(doctype)}`;
    return name ? `${base}/${encodeURIComponent(name)}` : base;
  }

  private async send(verb: "get" | "post" | "put" | "delete", url: string, data?: Doc) {
    const response = await this.context[verb](url, data ? { data } : {});
    if (!response.ok()) {
      throw new Error(`${verb.toUpperCase()} ${url}: ${await response.text()}`);
    }
    return response.json();
  }
}

/** Run a scheduled job now; it is enqueued, so callers poll for its effect. */
export async function runScheduledJob(api: Api, method: string) {
  const [job] = await api.list("Scheduled Job Type", { filters: { method } });
  await api.call("frappe.core.doctype.scheduled_job_type.scheduled_job_type.execute_event", {
    doc: JSON.stringify({ name: job.name }),
  });
}

/** Assert a raw request was refused for lack of permission. */
export async function expectDenied(pending: Promise<APIResponse>) {
  const response = await pending;
  const body = await response.text();
  expect(response.ok(), body).toBeFalsy();
  expect(body).toMatch(/PermissionError|not permitted|Insufficient Permission/i);
}
