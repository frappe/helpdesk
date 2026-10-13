# Helpdesk E2E tests

Playwright specs for the core user journeys, run against a real bench site.

## Run locally

```sh
bench new-site e2e.localhost --admin-password admin --install-app helpdesk
cd apps/helpdesk && yarn install --ignore-scripts && npx playwright install chromium
yarn build   # the webserver serves the built desk bundle

BASE_URL=http://localhost:8000 SITE_NAME=e2e.localhost yarn test:e2e
```

`SITE_NAME` sends `X-Frappe-Site-Name`, so no `/etc/hosts` entry is needed.
Set `ADMIN_PASSWORD` if the site's Administrator password is not `admin`.

## Layout

- `global.setup.ts` seeds the personas and saves a logged-in session for each.
- `helpers/` holds the REST client, personas, fixtures and data factories.
- `tests/` groups the specs by who uses the screen: `agent/`, `settings/`, `customer/` and `admin/`.
  Each spec creates its own data with unique names.
- `fixtures/` holds files the specs upload.

## Writing a spec

- Import `test`, `expect` and `uid` from `helpers/fixtures`, never from `@playwright/test`.
- Call `usePersona("agent")` at file or `describe` level to pick who `page` is. `pageAs` opens a second user.
- Seed over REST with `api`, `apiAs` or the `ticket` fixture. Click only through the flow under test.
- Assert what was saved with `api` after the UI action, not only what the screen shows.
- Give every record a `uid()` name so specs never depend on each other or on old runs.
- Restore anything site-wide you change. `snapshotSettings` does this for HD Settings.
- Title a test with a present-tense sentence about the behaviour, e.g. "comments post once, edit, delete and survive leaving the ticket".
- A bug the spec finds gets fixed in the same PR, or the test becomes `test.fixme` with a one-line comment naming the cause.
- Keep a folder under 15 specs. Split a growing area into its own folder under `tests/`.
