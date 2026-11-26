import { expect, test as setup } from "@playwright/test";
import { Api } from "./helpers/api";
import { skipGettingStarted } from "./helpers/fixtures";
import { seedSite } from "./helpers/seed";
import { siteHeader } from "./helpers/site";
import {
  PASSWORD,
  emailOf,
  storageStateOf,
  type PersonaKey,
} from "./helpers/personas";

const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || "admin";
const PERSONAS: PersonaKey[] = [
  "admin",
  "manager",
  "agent",
  "agent2",
  "customer",
  "customerManager",
];

setup("seed site and log every persona in", async ({ browser, baseURL }) => {
  const admin = await Api.login(baseURL!, "Administrator", ADMIN_PASSWORD);
  await seedSite(admin);

  for (const key of PERSONAS) {
    const context = await browser.newContext({
      baseURL,
      extraHTTPHeaders: siteHeader(),
    });
    const password = key === "admin" ? ADMIN_PASSWORD : PASSWORD;
    const response = await context.request.post("/api/method/login", {
      form: { usr: emailOf(key), pwd: password },
    });
    expect(response.ok(), `login as ${key}`).toBeTruthy();
    const page = await context.newPage();
    await skipGettingStarted(page, emailOf(key));
    await page.goto("/api/method/ping");
    await context.storageState({ path: storageStateOf(key) });
    await context.close();
  }
});

