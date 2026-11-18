# Test plan: Frappe Helpdesk, ticket workflows

| | |
|---|---|
| Plan version | 1.1 (see change log at the end) |
| System under test | frappe/helpdesk, https://github.com/frappe/helpdesk, AGPL-3.0, branch `version-16`, baseline commit `e326986329341c803dd4bf094322670ad0591ca5` (16.1.0), on Frappe Framework v16.56.0 (`49789a1`) |
| Team | three members (M1, M2, M3: replace with names and roll numbers) |

## 1. Scope

**In scope: two related workflows of the Ticket module.**

| Workflow | Starting condition | User action | Expected outcome |
|---|---|---|---|
| A. Raise a ticket | Customer signed in to the portal | Enters subject and description, submits | Ticket created: Open, Medium, raised by the customer, visible to them and to agents |
| B. Handle and close a ticket | An Open ticket exists | Agent triages, assigns, replies and resolves; customer closes and rates (or the daily job closes it) | Status, assignee, resolution date and rating stored per BR1–BR4 |

Shared record: the **HD Ticket** row (status, status category,
resolution date, rating, assignee), created by A and read and changed by B.
Its conversation (Communication rows) is written by both and read by the
auto-close job.

Requirements FR-A1…A4, FR-B1…B6 and business rules BR1–BR4 are listed in
`TRACEABILITY.md` (with sources in `e2e/USE_CASES.md` and
`unit/README.md`). Roles: **Agent** and **HD Customer** (customer portal
user).

**Out of scope:** email channels and email parsing, SLA calculation,
knowledge base, telephony, reports and dashboards, admin settings screens
(used only to set up data), mobile layout, upstream test suites (not
counted), production deployment (nginx, gunicorn, HTTPS).

## 2. Approach by risk level

Depth follows `RISK_REGISTER.md`:

| Level | Risks | Techniques and levels |
|---|---|---|
| High | PR-01 BR2, PR-02 BR3, PR-05 access, PR-08 accessibility | Unit MCC + MC/DC (BR2) or full state-transition coverage (BR3); mutation with custom operators; API decision tables and role-negative tests; Playwright flows and access matrix; axe + Lighthouse + keyboard test |
| Medium | PR-03 BR1, PR-04 BR4, PR-06 inputs, PR-07 duplicates, PR-10 components, PR-11 usability | EP and 3-point BVA from the OpenAPI generator; decision tables; repeated-request and recovery tests; ZAP passive and pip-audit; UC flows |
| Low | PR-09 performance | k6 at 1 and 5 users |

Test levels: unit (pytest + coverage.py, framework replaced by test
doubles), API and integration (pytest + Requests against the running site),
browser end-to-end (Playwright + Chromium), plus static analysis
(SonarQube), mutation (Cosmic Ray), usability/accessibility (Playwright,
axe-core, Lighthouse), security (Playwright, OWASP ZAP, pip-audit) and
performance (k6). Each executable case is counted once within its level.

## 3. Roles

| Member | Owns (examined on) | Use cases |
|---|---|---|
| M1 | Static analysis, white-box unit testing, mutation, CI quality gate | UC-01, UC-02 |
| M2 | API and integration testing, OpenAPI spec and data generator | UC-03, UC-04 |
| M3 | Use-case automation, usability and accessibility, security, performance | UC-05, UC-06 |
| All | Test management (this plan, estimates, risks, defects, progress, completion report), AI-use record | |

## 4. Environment

| | |
|---|---|
| Host | Windows 11, Intel i5-13420H, 12 logical CPUs; WSL2 Ubuntu 26.04.1, 7.6 GB RAM |
| Stack | Python 3.14.4, Node 24, MariaDB 11.8.6, Redis 8.0.5 (no RediSearch), bench 5.31.1 |
| Site | `helpdesk.localhost` on `bench serve` port 8000, developer mode |
| Tools | pytest 9.2, coverage.py 7.17.3, Cosmic Ray 8.9.0, Playwright 1.65.1 (Chromium), @axe-core/playwright 4.14.0, Lighthouse 13.6.0, OWASP ZAP 2.17.0, pip-audit 2.10.1, k6 2.4.0, SonarQube Community Build 26.11 + SonarScanner 8.4 |
| CI | GitHub Actions on the group's public fork https://github.com/ibbster05/helpdesk: `.github/workflows/sqe-quality-gate.yml` on every PR into `team/sqe-tests` (unit + coverage, mutation, SonarQube gate, API + browser on a live site); the "SQE gate" check is required by branch protection |

Set-up, start, seed and reset commands are in `tests/team/README.md` and
the scripts `seed.sh` and `run_*.sh`.

## 5. Test data

Synthetic only. `seed.sh seed` creates one agent (`agent.one@sqe.test`),
two customers (`customer.a@sqe.test`, `customer.b@sqe.test`) and the
settings the rules depend on; passwords are generated into the git-ignored
`tests/team/.env`. `seed.sh reset` deletes the test accounts' tickets and
linked rows and restores the settings (auto-close on, Replied, 7 days;
feedback mandatory). Each suite resets before it runs. API input values
come from `api/generated/testdata.json`, produced by
`api/generate_testdata.py` from `api/openapi.yaml`.

## 6. Schedule

| Week | Dates | Planned | Status (18 Nov) |
|---|---|---|---|
| 1 | 16–22 Nov 2026 | Environment and baseline; scope and test basis; unit + MCC/MC/DC; mutation; OpenAPI + generator + API tests; use cases + Playwright; usability/accessibility; security; performance; SonarQube | Done except the items below |
| 2 | 23–29 Nov 2026 | Public fork; members commit their own areas; GitHub Issues for the defect log; CI pipeline; blocked PR; documented fix PR (DEF-01 or DEF-02); RCA; risk review | Started early (18 Nov): fork, Issues #2–#36, CI gate (PR #1), blocked PR #37, fix PR #38 done; members' own commits and risk review open |
| 3 | 30 Nov–6 Dec 2026 | Regression on fixes; final weekly report; completion report; AI-use record; PDF and zip; viva rehearsal (each member reruns a test) | Not started |

The submission deadline is set by the course; the team adjusts weeks 2–3
to it.

## 7. Entry, exit, suspension and resumption criteria

**Entry** (per test level): baseline commit checked out and site running;
`seed.sh reset` succeeds; the level's tools installed and versions recorded;
the requirements it covers are in the traceability matrix.

**Exit criteria** (measurable; EC-1 to EC-3 tied to the highest risks):

| ID | Criterion | Target | Risks | Actual (18 Nov) | Met? |
|---|---|---|---|---|---|
| EC-1 | Unit tests on the business-rule scope | all pass; 100 % statement and branch coverage; mutation score ≥ 95 % | PR-01, PR-02, PR-03, PR-04 | 159 pass; 100 % / 100 %; 97.0 % | **Yes** |
| EC-2 | Open Major or Critical defects against BR1–BR4 | 0 | PR-02, PR-03 | 0 (DEF-01 fixed by PR #38) | **Yes** |
| EC-3 | Access decisions and access-control defects | 13 / 13 decisions as expected and 0 open Major access-control defects | PR-05 | 12 / 13; 2 open (DEF-02, DEF-03) | **No** |
| EC-4 | Performance of opening a ticket | p95 ≤ 800 ms at 5 users and < 1 % unexpected failures, in both runs | PR-09 | 27.7 / 25.8 ms; 0 % | **Yes** |
| EC-5 | Accessibility of the fixed key screen (customer ticket page) | Lighthouse accessibility ≥ 90 and 0 critical/serious axe violations | PR-08 | 100; 0 | **Yes** |
| EC-6 | Requirements coverage | 100 % of requirements and rules traced to executed tests | all | 14 / 14 | **Yes** |

**Release criteria** (the three shown in the final report): **RC-1 = EC-2**
(functional), **RC-2 = EC-3** (security), **RC-3 = EC-4** (performance).

**Suspension**: stop a test level when (a) the site or a dependency it needs
is down for more than an hour; (b) more than 30 % of a suite fails for an
environment reason (seed/reset error, server error unrelated to the test);
(c) a defect blocks sign-in or ticket creation, which every flow needs;
(d) the baseline changes unexpectedly.

**Resumption**: the cause is fixed and recorded; `seed.sh reset` succeeds;
a smoke set passes (one unit file, `test_create_ticket_input`, UC-01 MF);
then the suspended suite is rerun from the start.

## 8. Risks

See `RISK_REGISTER.md` (11 product, 5 project risks, 5 × 5 matrix).

## 9. Deliverables

Test scripts and data (`tests/team/`), reports per activity (`*/…REPORT.md`,
`api/WEAKNESSES.md`, `mutation/SURVIVORS.md`, `sonar/`), defect log
(`management/defects.yaml` → GitHub Issues), RCA (`management/RCA.md`),
weekly progress reports, test completion report, AI-use record.

## Change log

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-11-16 | Scope, workflows, rules and roles agreed; test levels chosen |
| 1.1 | 2026-11-18 | Plan written up with risks, estimates, criteria and week-1 status; recovery test and calibration added; SonarQube moved to port 9100 |
| 1.2 | 2026-11-18 | CI gate on the public fork; EC-2 met after the DEF-01 fix |
