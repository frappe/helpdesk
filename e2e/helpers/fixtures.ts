import { test as base, expect, type Browser, type Page } from "@playwright/test";
import { Api } from "./api";
import { raiseTicket } from "./factories";
import {
  PASSWORD,
  emailOf,
  storageStateOf,
  type PersonaKey,
} from "./personas";
import { siteHeader } from "./site";

const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || "admin";

interface Fixtures {
  /** REST client logged in as Administrator, for seeding and DB assertions. */
  api: Api;
  /** REST client for any persona, e.g. to act as the customer. */
  apiAs: (key: PersonaKey) => Promise<Api>;
  /** A second browser page logged in as another persona. */
  pageAs: (key: PersonaKey) => Promise<Page>;
  /** A fresh ticket the customer raised, for tests that need any one ticket. */
  ticket: Record<string, any>;
}

/** Log a spec file's `page` in as one persona. */
export function usePersona(key: PersonaKey) {
  test.use({ storageState: storageStateOf(key) });
}

export const test = base.extend<Fixtures>({
  api: async ({ baseURL }, use) => {
    await use(await Api.login(baseURL!, "Administrator", ADMIN_PASSWORD));
  },
  apiAs: async ({ baseURL }, use) => {
    await use((key) =>
      Api.login(baseURL!, emailOf(key), key === "admin" ? ADMIN_PASSWORD : PASSWORD)
    );
  },
  pageAs: async ({ browser, baseURL }, use) => {
    const contexts: Awaited<ReturnType<Browser["newContext"]>>[] = [];
    await use(async (key) => {
      const context = await browser.newContext({
        baseURL,
        extraHTTPHeaders: siteHeader(),
        storageState: storageStateOf(key),
      });
      contexts.push(context);
      return context.newPage();
    });
    await Promise.all(contexts.map((context) => context.close()));
  },
  ticket: async ({ apiAs }, use) => {
    await use(await raiseTicket(await apiAs("customer")));
  },
});

export { expect };
export { uid } from "./factories";

/** Hide the getting started panel that covers the sidebar for admins and managers. */
export function skipGettingStarted(page: Page, user: string) {
  const key = `isOnboardingStepsCompletedhelpdesk${user}`;
  return page.addInitScript((key) => localStorage.setItem(key, "true"), key);
}
