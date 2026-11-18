# Weekly progress report: week 1 (16–22 Nov 2026), status on 18 Nov

## 1. Progress against the plan

| Area (ESTIMATION.md #) | Planned for week 1 | Status | Evidence |
|---|---|---|---|
| 1 Environment, baseline, scope | done | **Done**: bench, site, seed/reset; scope approved 16 Nov | `seed.sh`, `TEST_PLAN.md` |
| 2 SonarQube + cyclomatic complexity | done | **Done** 18 Nov | `sonar/` |
| 3 Unit, MCC, MC/DC | done | **Done**: 159 tests, 100 % / 100 % | `unit/`, `reports/unit/` |
| 4 Mutation | done | **Done**: 86.9 % → 97.0 %, all 31 survivors of run 1 analysed (24 killed, 7 equivalent) | `mutation/SURVIVORS.md` |
| 5 CI gate and PRs | week 2 | Not started (needs the fork) | – |
| 6–7 API tests, OpenAPI, generator | done | **Done**: 127 tests (113 pass, 14 pinned weaknesses); 58 generated cases; constraint change shown | `api/` |
| 8 Use cases + Playwright | done | **Done**: 6 use cases, 32 flows, all automated and passing | `e2e/` |
| 9 Usability and accessibility | done | **Done**: 2 task tests, scans before/after, one screen fixed | `a11y/` |
| 10 Security | done | **Done**: 13 access decisions, 5 controls, ZAP, pip-audit | `security/` |
| 11 Performance and recovery | done | **Done**: 4 k6 runs within limits; R1, R2 pass | `perf/` |
| 12 Test management | week 2 | **Ahead**: plan, risks, estimates, traceability, defect log, RCA drafted 18 Nov | `management/` |
| 13 Report, AI record, viva | week 3 | Not started | – |

Of the 13 areas, 10 are done, 1 is drafted early and 2 are not started.
That is ahead of plan for the testing work, but **behind on everything that
needs the public repository**: no commits, no Issues, no CI.

## 2. GQM

**Goal:** assess the quality of the two ticket workflows, from the point of
view of the release decision, so the team can recommend release or hold.

| Question | Metric | Value (18 Nov) | Reading in context |
|---|---|---|---|
| Q1 How defect-prone is the code under test? | Defect density, backend: defects rooted in Python code / Python KLOC | 15 / 13.9 = **1.08 per KLOC** | Most backend defects come from the targeted tests, not a uniform sweep, so this is a lower bound for the app and not comparable to industry averages. |
| | Defect density, `hd_ticket.py` | 5 / 1.25 = **4.0 per KLOC** | The file that holds BR1–BR3 and assignment is about four times as defect-dense as the backend average. It is also Sonar's most complex file (cyclomatic 298). That supports putting the High risks there. |
| Q2 How completely are the requirements tested? | Requirements coverage, tested | 14 / 14 = **100 %** | Every requirement and rule has tests at two or more levels. |
| | Requirements coverage, passing | 9 / 14 = **64 %** | Five rows fail on three Major defects (DEF-01, DEF-02, DEF-03); the gap is concentrated, not spread. |
| Q3 Are fixes holding? | Reopen rate: reopenings / fixed defects | 0 / 2 = **0 %** | Only two fixes so far (A11Y-04, A11Y-11, re-scanned), so the rate says little yet. It becomes meaningful after the week-2 fix PRs. |

Supporting figures: 33 defects counted (9 Major, 16 Minor, 8 Trivial), 31
open; Pareto: accessibility 30 %, then business rule, error handling and
usability at 12 % each. By count, accessibility dominates. That is partly
because each axe rule is logged separately. By severity, the Majors that
block release are in business rules and access control.

## 3. Deviations from the plan

| Deviation | Cause | Effect |
|---|---|---|
| SonarQube moved from week 2 to week 1 | Ready earlier | None; frees week 2 |
| Test management drafted in week 1 | Needed to steer the remaining work | Estimates for done areas are not blind (stated in `ESTIMATION.md`) |
| Environment problems: Playwright upgrade, missing RediSearch, port clash between Sonar and Frappe realtime | PJ-01 | About half a day lost in total (team to confirm from their logs) |
| Nothing committed yet | Fork URL not decided | Commit history (a viva check) does not yet show who did what (PJ-03) |

## 4. Control actions for week 2

| # | Action | Owner | Due | Addresses |
|---|---|---|---|---|
| 1 | Create the public fork; each member commits their own area from `tests/team/` (one commit series per area, own name) | All | 23 Nov | PJ-03, PJ-04 |
| 2 | File the defect log as GitHub Issues (`tools/file_issues.py --repo … --execute`) and triage in a short meeting | All | 24 Nov | defect management |
| 3 | Build the CI pipeline; make the blocked PR (for example a test removed or a threshold breached) and the fix PR for DEF-01 using RCA-1's corrective action | M1 | 27 Nov | PJ-04, PR-02, EC-2 |
| 4 | Fix PR for DEF-02 / DEF-03 (`agent_only` + target check); rerun the access matrix | M2, M3 | 28 Nov | PR-05, EC-3 |
| 5 | Each member starts a time log and fills Actual for their areas | All | ongoing | estimation comparison |
| 6 | Each member reruns one of their tests and explains the assertions to the others | All | 29 Nov | PJ-03 (viva) |
| 7 | Start the AI-use record from the prompts kept so far | All | 29 Nov | PJ-03 |
