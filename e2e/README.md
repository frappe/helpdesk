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
