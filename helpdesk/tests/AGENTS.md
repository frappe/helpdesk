# Backend tests

Python tests for the Helpdesk server code, run with Frappe's test runner against a real site.

## Layout

- `helpdesk/tests/api/` mirrors `helpdesk/api/`. `helpdesk/api/contact.py` is tested in `helpdesk/tests/api/test_contact.py`, and `helpdesk/api/settings/email.py` in `helpdesk/tests/api/settings/test_email.py`.
- DocType tests stay next to their DocType (`helpdesk/helpdesk/doctype/<name>/test_<name>.py`), as Frappe expects.
- All backend test helpers (factories, toggles, fixture builders) live in `helpdesk/test_utils.py` and are imported from there, never defined inline in a test file. Check it before writing one (`make_ticket`, `create_agent`, `create_contact`, `create_customer`, `make_sla`, `make_team` and more); if it is missing, add it there with a docstring.
- Keep a folder under 15 files. Fold a small API module into the test file of its closest neighbour rather than giving it its own file.
- Every test folder needs an `__init__.py`.

## Running

Start the bench's redis first. Without it, saves fail with `Should not fail silently in tests` from the global search queue.

```bash
bench --site <site> run-tests --app helpdesk --module helpdesk.tests.api.test_contact
bench --site <site> run-tests --app helpdesk --module helpdesk.tests.api.test_contact --test test_edit_keeps_user_photo
bench --site <site> run-tests --app helpdesk            # everything, as CI does
```

The site needs `allow_tests` set. `before_tests` in `test_utils.py` seeds the SLA, holiday list and email account once per run; pass `--skip-before-tests` to reruns once that is done. CI (`.github/workflows/server-tests.yml`) runs the whole app with `--coverage`.

## Writing a test

- **Base class.** Subclass `FrappeTestCase` (`frappe.tests.utils`) or `IntegrationTestCase` (`frappe.tests`). Both give `self.set_user` and `self.freeze_time`, and both roll back after the class.
- **Call the API directly.** Import the whitelisted function and call it as Python. This skips the HTTP layer, so `@frappe.whitelist(methods=...)` and `allow_guest` are not exercised; test the permission checks inside the function instead.
- **Act as a persona.** Seed as Administrator, then switch for the call under test with `with self.set_user(agent.name):`. The context manager restores the user even when the test fails, so there is no `tearDown` to write.
- **Test who may not.** For every write endpoint, assert the role that must be refused: `with self.assertRaises(frappe.PermissionError):`. An agent calling a manager-only API is the most common bug here.
- **Assert saved state.** After the call, read back from the database (`frappe.db.get_value`, `doc.reload()`), not just the return value.
- **Unique data.** The database rolls back after each test class, not after each test, so records from one test are still there in the next. Give records unique names (`frappe.generate_hash(length=6)` in an email or title) or create them in `setUp`.
- **Settings.** Change a setting with `change_settings` from `frappe.tests.utils`: `with change_settings("HD Settings", {"field": value}):`. It restores the old value on exit.
- **Time.** Freeze the clock with `with self.freeze_time("2026-01-05 10:00:00"):` for SLA, dashboard and stats tests. Never assert against `now()` taken outside the block.
- **No commits.** Never call `frappe.db.commit()` or `rollback()` in a test. It leaks data into other tests.
- **Names.** Test classes are `Test<Thing>`, test methods say what happens: `test_agent_cannot_delete_contact`, not `test_delete_2`.
- **What to cover.** Important behaviour and edge cases (empty input, missing links, a second customer, a disabled record). Skip trivial getters, and merge small checks into one test rather than one test per assertion. If personas are involved, test each persona in its own method. If a test is long, break it into helper methods with descriptive names. 
- **What not to cover.** Don't test Frappe itself, or the Python standard library. Don't test the HTTP layer, or the UI. Don't test the database engine. Don't test the email server. Don't test third-party libraries. Don't test your own code that is already tested by Frappe (e.g., `frappe.get_doc`, `frappe.db.get_value`, `frappe.sendmail`).
- **Test data.** Don't hard-code a record's name or email address. Use the factories in `test_utils.py` to create them, and give them unique names. If you need a specific name, create it in `setUp` and delete it in `tearDown`.
- **Test isolation.** Each test should be independent. Don't rely on the order of tests, or on data created by other tests. Use `setUp` to create any necessary data, and `tearDown` to clean up if needed.
- **Test coverage.** Aim for high test coverage, but don't sacrifice quality for quantity. Focus on testing the most critical and complex parts of the code. DO NOT write tests just to increase coverage numbers. DO NOT weaken assertions to make tests pass. If a test fails, investigate and fix the underlying issue. DO NOT CHANGE the code under test to make a test pass without understanding why it failed. If a test fails, it indicates a potential bug or unexpected behavior that needs to be addressed.


## When a test finds a bug

- A small, clear fix ships in the same PR as its own `fix:` commit, with the test that caught it.
- A bigger one gets reported. Mark the test `@unittest.expectedFailure` with a one-line comment naming the cause, so it starts passing loudly once fixed. Never weaken the assertion to make it pass.
