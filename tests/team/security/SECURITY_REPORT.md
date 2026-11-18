# Defensive security assessment

Scope: the two ticket workflows (A raise a ticket, B handle a ticket) on the
team's local copy of helpdesk 16.1.0 (commit e326986) and frappe 16.56.0,
with synthetic accounts only. Method: passive observation, source review and
normal application actions. No active scan, spider, fuzzing or exploit was
run.

| Tool | Version | Used for |
|---|---|---|
| Playwright + Chromium | 1.65.1 | access decisions and control checks as each role |
| OWASP ZAP | 2.17.0 (daemon, passive rules only, 59 of 59 enabled, auto-update off) | proxy and passive scan while the browser tests ran |
| pip-audit | 2.10.1 | Python dependency audit (PyPI / OSV advisories) |

Scripts: `e2e/security/access_matrix.spec.mjs`, `e2e/security/controls.spec.mjs`,
`security/zap_passive.sh`, `security/zap_summary.py`, `security/dependency_audit.sh`.
Evidence: `security/evidence/`.

## 1. Attack surface: routes and data of the two workflows

Routes were taken from the source and confirmed by ZAP, which saw 7,535
requests to 293 distinct URLs while all 52 browser tests (32 use-case flows,
2 usability tasks, 18 security checks) ran through it
(`evidence/zap/urls.json`, route list in `evidence/zap/zap_summary.md`).

| Workflow step | Route | Data read or written |
|---|---|---|
| sign in / out | `POST /api/method/login`, `POST /api/method/logout` | email, password; sets `sid` and four display cookies |
| A: open form | `GET /helpdesk/my-tickets/new`; `GET .../hd_ticket_template.api.get_one` | template fields |
| A: suggestions while typing | `GET /api/method/helpdesk.api.article.search` | subject text |
| A: submit | `POST /api/method/helpdesk.helpdesk.doctype.hd_ticket.api.new` | subject, description -> HD Ticket (raised_by, status, priority, key); Communication |
| A/B: read ticket | `GET .../hd_ticket.api.get_one`, `GET /helpdesk/my-tickets/{id}`, `GET /helpdesk/tickets/{id}` | ticket fields, conversation, contact |
| B: list | `POST /api/method/helpdesk.api.doc.get_list_data`, `GET /api/resource/HD Ticket` | tickets the user may see |
| B: status, priority, type, feedback | `PUT /api/resource/HD Ticket/{id}`, `frappe.client.set_value` | status, status_category, resolution_date, priority, ticket_type, feedback, feedback_rating |
| B: assign | `POST /api/method/run_doc_method` (`assign_agent`), `frappe.desk.form.assign_to.add` | ToDo, `_assign`, DocShare |
| B: reply | `POST run_doc_method` (`create_communication_via_contact` / `reply_via_agent`) | Communication |
| back office | `/app/*` (redirects to `/desk/*`) | every doctype, for desk users only |

Sensitive data on these routes: customer email and name, ticket text, the
ticket's `key` (authenticates guest feedback links; agents only), and the
session id.

## 2. Access matrix

Roles: **Customer** (HD Customer) and **Agent**; a second customer and a
visitor who is not signed in are used for the denied cases. Expected
decisions come from the business rules (BR4), the DocType permissions in
`hd_ticket.json`, and `has_permission` in `hd_ticket.py`.

| Action | Customer (own ticket) | Customer (other's ticket) | Agent | Not signed in |
|---|---|---|---|---|
| Raise a ticket | allow (AC-01) | - | allow | deny |
| Read the ticket | allow (AC-02) | deny (AC-03) | allow (AC-09) | deny (AC-13) |
| Set status to Resolved | deny (AC-04) | deny | allow (AC-10) | deny |
| Change priority | deny (AC-05) | deny | allow | deny |
| Assign an agent | deny (AC-08) | deny | allow (AC-11) | deny |
| Delete a ticket | deny | deny | deny (AC-12) | deny |
| Open the agent desk screen | deny (AC-06) | deny | allow | deny |
| Open the back office (`/app`) | deny (AC-07) | deny | allow | deny |

### Automated access decisions (13)

Each check runs in Chromium as the role, sending requests from inside the
running app with its own session cookie and CSRF token. Raw records:
`evidence/access_matrix.json` / `.md`; screenshots in `evidence/screens/`.

| ID | Role | Action | Expected | Observed | Evidence |
|---|---|---|---|---|---|
| AC-01 | Customer | raise a ticket | allowed | allowed | HTTP 200; stored raised_by = the customer |
| AC-02 | Customer | read own ticket | allowed | allowed | HTTP 200 |
| AC-03 | Customer B | read customer A's ticket | denied | denied | screen "Not allowed via controller permission check", returned to own list (screenshot); API HTTP 403 |
| AC-04 | Customer | set status to Resolved | denied | denied | HTTP 403 "You cannot change Status after the ticket is raised"; stored status Open |
| AC-05 | Customer | change priority | denied | denied | HTTP 403 "You do not have permission to change Priority"; stored Medium |
| AC-06 | Customer | open agent ticket screen | denied | denied | redirected to `/helpdesk/my-tickets/{id}`; no agent controls (screenshot) |
| AC-07 | Customer | open back-office ticket list | denied | denied | HTTP 403 at `/desk/hd-ticket` (screenshot) |
| **AC-08** | Customer | assign an agent to own ticket | **denied** | **allowed** | HTTP 200; ticket now assigned to the agent. **Finding SEC-01** |
| AC-09 | Agent | read a customer's ticket | allowed | allowed | HTTP 200 |
| AC-10 | Agent | set status to Resolved | allowed | allowed | HTTP 200; stored Resolved |
| AC-11 | Agent | assign an agent | allowed | allowed | HTTP 200; assignee recorded |
| AC-12 | Agent | delete a ticket | denied | denied | HTTP 403 "does not have doctype access via role permission"; ticket still stored |
| AC-13 | Not signed in | read a ticket | denied | denied | HTTP 403 "Login to access" |

On the baseline, 12 of 13 decisions matched. AC-08 was recorded as an
expected failure, so the suite stayed green while the finding was open.

**Update 18 Nov 2026:** SEC-01 (DEF-02) and the related W-API-06 (DEF-03)
are fixed by PR #41. `assign_agent` is now `agent_only` and accepts only
agents as targets. AC-08 is now an ordinary passing check, observed as
"denied" with HTTP 403 and no assignee. **13 of 13 decisions match.** The
table above keeps the baseline observation as evidence; the CI run of
PR #41 holds the new one.

## 3. Security controls reviewed

Observed through the app (`evidence/controls.json` / `.md`) and corroborated
in the source.

| ID | Control | Observed | Source / configuration | Verdict |
|---|---|---|---|---|
| CT-01 | Session cookie attributes | `sid`: HttpOnly, SameSite=Lax, Secure=false, lifetime about 170 h; not readable from page scripts | `frappe/auth.py` `CookieManager.set_cookie`: `samesite="Lax"`, `secure` only when the request scheme is https; `sid` set with `httponly=True`; expiry from System Settings `session_expiry` (default 240 h) | pass; Secure depends on HTTPS in production |
| CT-02 | CSRF token | browser-session POST without `X-Frappe-CSRF-Token`: HTTP 400 CSRFTokenError, nothing created; with it: 200 | `auth.py` `validate_csrf_token`: enforced for unsafe methods when the session holds a token; skipped if `ignore_csrf` is set (it is not) or for sessions that never loaded the app (API-only logins); the app sends `window.csrf_token` (frappe-ui `frappeRequest.ts`) | pass |
| CT-03 | Session ends at sign-out | replaying the old `sid` after logout: HTTP 401 | server-side session store; logout deletes the session | pass |
| CT-04 | No account enumeration at sign-in | wrong password and unknown account both HTTP 401 "Invalid login credentials" | `LoginManager` returns one message for both | pass |
| CT-05 | Role checks on the server | the customer screen has no priority control, and the same change sent directly is refused (403); stored value unchanged | `customer_edit_controller.prevent_customer_edits` and permlevel 7 on `priority` | pass |
| CT-06 | Role check on assignment | a customer can assign (AC-08) | `frappe/handler.py run_doc_method` only checks that the user can load the document (`get_doc(..., check_permission=True)`) and that the method is whitelisted; `HDTicket.assign_agent` has no role check, and HD Customer has read/write on own tickets | **fail: SEC-01** on the baseline; **pass since PR #41** (`agent_only` plus a target check) |
| CT-07 | Security headers | dev server sends no CSP, X-Frame-Options or X-Content-Type-Options (ZAP) | Bench's production nginx template adds X-Frame-Options SAMEORIGIN, X-Content-Type-Options nosniff, HSTS and Referrer-Policy, but **no Content-Security-Policy** | partial: SEC-03 |
| CT-08 | No known-vulnerable sanitiser in the served code (Playwright, added with PR #42) | reads every Helpdesk script the page loads and extracts the embedded DOMPurify version; requires 3.4.17 or later | `desk/yarn.lock` entry for `dompurify@^3.4.0` | **fail: SEC-02** on the baseline ("DOMPurify 3.4.8"); **pass since PR #42** (3.4.18) |

## 4. ZAP passive findings

Full report: `evidence/zap/zap_report.html`; grouped table:
`evidence/zap/zap_summary.md`.

| ZAP alert (risk) | Instances | Assessment | Finding |
|---|---|---|---|
| Vulnerable JS Library (High) | 1 | Real. The Helpdesk bundle contains DOMPurify 3.4.8 (locked in the baseline `desk/yarn.lock` through frappe-ui `^3.4.0`); ZAP lists eight CVEs. DOMPurify sanitises ticket HTML in the browser, so a bypass would reach customer-supplied content. *Correction (18 Nov):* this row first said "fixed by 3.4.16"; OSV shows three of the eight fixed only in 3.4.17. **After PR #42** (`evidence/zap_after_def14/`): 0 instances | SEC-02 |
| Content Security Policy Header Not Set (Medium) | 32 | Real in development and in the Bench production config | SEC-03 |
| Missing Anti-clickjacking Header (Medium) | 31 | Development server only; production nginx adds X-Frame-Options | note |
| Sub Resource Integrity Attribute Missing (Medium) | 1 | Same-origin stylesheet built at run time; SRI adds little for same-origin assets | accepted |
| Application Error Disclosure (Low) | 1 | `helpdesk.api.article.search` returns 500 because Redis lacks RediSearch (also UX-03) | SEC-05 |
| Cookie No HttpOnly Flag (Low) | 20 | `full_name`, `user_id`, `system_user`, `user_lang` are readable by scripts; `user_id` is the email address. The session cookie is HttpOnly | SEC-04 |
| Server Leaks Version via "Server" header (Low) | 302 | `Werkzeug/3.1.9 Python/3.14.4` from the development server; production runs gunicorn behind nginx | note |
| X-Content-Type-Options Header Missing (Low) | 295 | Development server only; production nginx sets `nosniff` | note |
| Timestamp Disclosure (Low) | 23 | False positive: numbers in bundled library code | none |
| Sensitive Information in URL (Info) | 1 | False positive: `ticket=` is a ticket number, not a secret | none |
| Suspicious Comments (Info) | 5 | Licence text and comments in bundled code | none |
| Modern Web Application (Info) | 31 | Informational | none |

## 5. Dependency audit

`pip-audit --no-deps --disable-pip` against the exact versions installed in the
bench environment: **178 packages** checked
(`evidence/dependencies/audited_requirements.txt`). Four locally installed
packages cannot be checked by version and are listed in `local_apps.txt`:
the apps frappe, helpdesk and telephony (the code under test) and the team's
own mutation-operator plugin. Results: `pip_audit.json`, `pip_audit.md`.

pip-audit reported 11 entries; one pdfkit entry is listed twice, so **10
distinct advisories in 3 packages**.

| Component | Advisories | Fixed in | Reachable from the workflows? | Impact here | Recommendation |
|---|---|---|---|---|---|
| bleach 6.3.0 | GHSA-g75f-g53v-794x (ReDoS in `linkify(parse_email=True)`), GHSA-gj48-438w-jh9v (`formaction` URI not sanitised), GHSA-8rfp-98v4-mmr6 (XSS bypass in `clean` with `a href`) | 6.4.0 (two), none (one) | No. Frappe sanitises with `nh3` (`frappe/utils/html_utils.py`); it imports only `bleach_allowlist`, a list of tag and style names. No Frappe or Helpdesk code calls `bleach.clean` or `linkify` | Low: installed but not on the request path | upgrade to 6.4.0 when Frappe allows; add a guard test that the sanitiser stays nh3 |
| gitpython 3.1.62 | CVE-2026-114145, -110859, -110858, -110856, -110857, -110855 (submodule/hook, refspec option injection, ReDoS, env expansion) | 3.2.0 / 3.2.1 | No. Used by `frappe/utils/boilerplate.py` (new-app scaffolding) and `frappe/gettext/translate.py`, which are developer commands, not web requests | Low | upgrade to 3.2.1 |
| pdfkit 1.0.0 | PYSEC-2026-2860 / CVE-2025-26240 (`from_string` runs JavaScript, reads local files) | none | Partly. Printing a ticket to PDF passes customer-written HTML to wkhtmltopdf; wkhtmltopdf is not installed on this site, so the path is inert here | Mitigated: `frappe/utils/pdf.py` line 119 always adds `disable-javascript` and `disable-local-file-access`, the two capabilities the exploit needs | keep those options; prefer the Chrome PDF generator Frappe 16 offers |

## 6. Findings

Each finding is a GitHub Issue: SEC-01 = DEF-02 (#3), SEC-02 = DEF-14 (#15),
SEC-03 = DEF-15 (#16), SEC-04 = DEF-16 (#17), SEC-05 = DEF-13 (#14), with
severity, priority and triage in `management/defects.yaml`. They are linked
to risks PR-05 (access control) and PR-10 (components) in the risk register.
SEC-01 and SEC-02 are fixed (PRs #41 and #42).

| ID | Finding | Evidence | Root cause | Severity | Likely impact | Recommended correction |
|---|---|---|---|---|---|---|
| SEC-01 | A customer can assign an agent to their own ticket (= W-API-05) | AC-08; API test `test_customer_cannot_assign_an_agent` | `assign_agent` is whitelisted with no role check; `run_doc_method` checks only document permission, which the ticket's owner has | Major | customers can choose or pester agents, bypass routing, and generate assignment notifications | decorate `assign_agent` with Helpdesk's existing `agent_only` (or check `is_agent()`) and add a regression test. **Fixed by PR #41 (DEF-02)** |
| SEC-02 | Bundled DOMPurify 3.4.8 has eight published CVEs | ZAP 10003 on `index-*.js` | lockfile pins 3.4.8 inside frappe-ui's `^3.4.0` range | Major (proposed; not exploited here) | a sanitiser bypass could run script from ticket content in another user's browser | update the lock to DOMPurify 3.4.17 or later and rebuild. **Fixed by PR #42 (DEF-14)**: lock entry 3.4.18 (OSV: no advisory); CT-08 passes and ZAP no longer reports a vulnerable library |
| SEC-03 | No Content-Security-Policy, including in the production nginx template | ZAP 10038; Bench `nginx.conf` template | not configured by Bench or Frappe | Minor | no second line of defence if an XSS gets through | add a CSP (start report-only) in the nginx site config |
| SEC-04 | `user_id` (email) and `full_name` cookies readable by scripts | ZAP 10010 | Frappe sets them for the UI without HttpOnly | Minor | any XSS can read the user's identity; the session itself stays protected | accept, or serve these values from the boot data instead of cookies |
| SEC-05 | Search endpoint returns 500 with a stack trace when RediSearch is absent | ZAP 90022; server log `unknown command 'FT.SEARCH'` | no fallback when the Redis module is missing | Minor | leaks internals; noisy errors for customers (UX-03) | catch the missing-module error and return an empty result; deploy Redis Stack |

Verified controls (no finding): HttpOnly and SameSite session cookie, CSRF
token on browser sessions, server-side session end at logout, uniform
sign-in errors, server-side field and role checks for status and priority,
ticket privacy between customers, back-office access, delete permission.

Not covered: HTTPS-only behaviour (Secure cookie, HSTS) because the site runs
on plain HTTP; the production nginx headers were read from the template, not
observed; the JavaScript dependencies were not audited by version beyond
what ZAP's library check found.

## How to rerun

```
cd ~/frappe-bench/apps/helpdesk/tests/team
(cd e2e && npx playwright test security)      # access matrix + controls
bash security/zap_passive.sh                  # ZAP passive during all browser tests
bash security/dependency_audit.sh             # pip-audit
```
