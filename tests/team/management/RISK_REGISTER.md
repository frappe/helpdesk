# Risk register

Written down on 2026-11-18. The inherent scores record the reasoning
that set the depth of each activity when the scope was fixed on
2026-11-16 (the team should review them); the residual column comes from
the test results up to 2026-11-18. Score = likelihood (L) ×
impact (I), each 1–5.

| Level | Score | What the level decides |
|---|---|---|
| **High** | 15–25 | Tested at three or more levels; strongest white-box technique (MCC + MC/DC or every state transition); mutation testing; negative and role-based tests; at least one exit criterion tied to the risk. |
| **Medium** | 8–14 | Two levels; EP + 3-point BVA or decision table on every input of the rule; at least one end-to-end flow. |
| **Low** | 1–7 | One level or a tool scan; smoke depth. |

Likelihood scale: 1 rare … 5 almost certain (judged from code complexity,
Sonar figures, how often the area changes upstream and how many conditions
it has). Impact scale: 1 cosmetic … 5 data loss, data disclosure or a
workflow that cannot be completed.

## Product risks

| ID | Risk (what could go wrong) | L | I | Score | Level | Technique and depth chosen | Owner | Materialised as | Residual (18 Nov) |
|---|---|---|---|---|---|---|---|---|---|
| PR-01 | BR2 feedback rule evaluated wrongly: a resolved ticket closes without a rating, or a customer is blocked from closing | 3 | 5 | 15 | High | Critical module: MCC (32 rows) and MC/DC pairs at unit level; mutation incl. custom operators (agent exemption); decision-table API tests; UC-02 all flows; keyboard task test | M1 | DEF-04 (minor) | **Low**: every condition shown to flip the outcome; 100 % killable mutants killed |
| PR-02 | BR3 resolution date wrong after a change of state (missing, not cleared, re-stamped) | 4 | 4 | 16 | High | State-transition testing: every allowed transition and one disallowed from each state (unit + API); repeated requests; recovery test R2; UC-04/05 postconditions | M1, M2 | **DEF-01 (Major, closed by PR #38)**, DEF-05 | Low: DEF-01 fixed and re-tested in CI; tickets the job closed before the fix still lack a date until the RCA-1 data repair |
| PR-03 | BR1 auto-close boundary off by one, or closes the wrong tickets | 3 | 4 | 12 | Medium | 3-point BVA (N−1, N, N+1) at unit and API level against real stored dates; EP on status and setting; repeat-run idempotency | M2 | DEF-01 (shared with PR-02, closed), DEF-11 | Low: boundary correct; DEF-01 fixed |
| PR-04 | BR4 lock fails: a customer changes a closed or rated ticket, or agent-only fields | 3 | 4 | 12 | Medium | Decision table (closed × rated × role) at unit and API level; field-level negative tests; UC-02 EF3, UC-05 EF2; CT-05 | M1, M3 | – | Low |
| PR-05 | Unauthorised access: a role or another customer reads or changes a ticket | 3 | 5 | 15 | High | Access matrix (13 decisions, Playwright); API negative tests per endpoint and role; source review of permission hooks; ZAP passive | M3, M2 | **DEF-02, DEF-03 (Major, closed by PR #41)** | Low: both fixed and re-tested in CI; 13 / 13 access decisions as expected; preventive method × role test (RCA-2) still to write |
| PR-06 | Invalid input accepted, or server errors (5xx) on bad input | 4 | 2 | 8 | Medium | Generated EP + 3-point BVA for every input of four operations (58 cases); API coverage criteria | M2 | DEF-06…09, DEF-12, DEF-13, DEF-32 | Medium: no data corruption seen, but 5xx with tracebacks remain |
| PR-07 | Duplicate or half-written records after retries or failures | 2 | 4 | 8 | Medium | Repeated-request tests on create, resolve, assign, close; failure-and-recovery tests R1, R2 | M2, M3 | DEF-10 (trivial) | Low |
| PR-08 | Accessibility barriers stop assistive-technology users completing a use case | 5 | 3 | 15 | High | axe-core + Lighthouse on the five key screens; keyboard-only task test; fix one screen and re-scan | M3 | DEF-17…26 | Medium: S2 fixed (Lighthouse 82→100, axe 6→0); P1 issues open on S1, S4, S5 |
| PR-09 | Ticket page too slow when several agents work at once | 2 | 3 | 6 | Low | k6 smoke: 1 and 5 users, twice each, p95 and failure-rate limits | M3 | – | Low: p95 ≤ 28 ms vs 800 ms limit |
| PR-10 | Vulnerable or misconfigured components (libraries, headers, cookies) | 3 | 4 | 12 | Medium | ZAP passive during the workflows; pip-audit of 178 Python packages; source and config review of cookies, CSRF, headers | M3 | DEF-14 (Major, closed by PR #42), DEF-15, DEF-16 | Low: DOMPurify 3.4.18, checked in the served bundle by CT-08 and ZAP; no CSP (DEF-15) remains |
| PR-11 | Users cannot find a ticket or understand why an action is unavailable | 3 | 3 | 9 | Medium | Usability task tests; UC-06 flows; observations during automation | M3 | DEF-28…31, DEF-35 | Medium |

## Project risks

| ID | Risk | L | I | Score | Level | Mitigation | Owner | Status (18 Nov) |
|---|---|---|---|---|---|---|---|---|
| PJ-01 | Local environment unstable (WSL bench, Redis without RediSearch, browser libraries on a new Ubuntu) and blocks test runs | 4 | 3 | 12 | Medium | Scripted start (`~/start.sh`), seed and reset (`seed.sh`), versions pinned in reports; issues logged as found | All | Occurred: Playwright 1.56 unsupported on Ubuntu 26.04 (upgraded to 1.65.1); RediSearch missing (DEF-13). Under control. |
| PJ-02 | Flaky browser tests from shared data or timing | 3 | 3 | 9 | Medium | Reset before each suite, one worker, unique subjects per test, assertions on stored state | M3 | Occurred: ambiguous locators and a rating-dialog click that needed a retry, fixed during UC work; the 32 flows now pass in one run. Occurred again on the CI runner: UC-05 EF2/AF2 failed in 2 of 3 runs. Cause was a product race (DEF-35), not the tests; the tests now fix the response order and one pinned test reproduces DEF-35 |
| PJ-03 | A member cannot explain AI-assisted work in the viva, or commit history is uneven | 3 | 5 | 15 | High | Area ownership; each member reruns and explains their tests before submission; AI-use record with prompts; members commit their own work | All | **Open**: all commits so far are under one member's name (the three area commits, the CI and fix PRs); AI-use record not yet written |
| PJ-04 | Public fork and GitHub Actions (SonarQube, all suites, mutation) not ready in time for the blocked and fix PRs | 3 | 4 | 12 | Medium | Build the pipeline from the existing scripts; start Sonar in the job; run the long suites on PRs only | M1 | **Closed** 18 Nov: fork https://github.com/ibbster05/helpdesk; gate required on `team/sqe-tests`; blocked PR #37 and fix PR #38 done |
| PJ-05 | Schedule overrun: many activities for three members | 3 | 3 | 9 | Medium | Three-point estimates, weekly progress against plan, control actions | All | On track for testing activities; CI and reporting remain |

## 5 × 5 matrix (inherent scores)

| Likelihood ↓ / Impact → | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| **5** | | | PR-08 | | |
| **4** | | PR-06 | PJ-01 | PR-02 | |
| **3** | | | PR-11, PJ-02, PJ-05 | PR-03, PR-04, PR-10, PJ-04 | PR-01, PR-05, PJ-03 |
| **2** | | | PR-09 | PR-07 | |
| **1** | | | | | |

Highest risks: PR-02 (16), PR-01, PR-05, PR-08, PJ-03 (15). Exit criteria
EC-1, EC-2 and EC-3 in the test plan are tied to PR-01, PR-02 and PR-05.

## Findings linked to risks

Every API, accessibility, security and performance finding is in
`defects.yaml` with its risk IDs; `generated/DEFECT_SUMMARY.md` lists them.
No finding was left without a risk except DEF-33 and DEF-34 (static code
quality, no user-facing risk) and the rejected DEF-27.
