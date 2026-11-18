# Weekly progress report: week 1 (16–22 Nov 2026), status on 18 Nov

## 1. Progress against the plan

| Area (ESTIMATION.md #) | Planned for week 1 | Status | Evidence |
|---|---|---|---|
| 1 Environment, baseline, scope | done | **Done**: bench, site, seed/reset; scope approved 16 Nov | `seed.sh`, `TEST_PLAN.md` |
| 2 SonarQube + cyclomatic complexity | done | **Done** 18 Nov | `sonar/` |
| 3 Unit, MCC, MC/DC | done | **Done**: 159 tests, 100 % / 100 % | `unit/`, `reports/unit/` |
| 4 Mutation | done | **Done**: 86.9 % → 97.0 %, all 31 survivors of run 1 analysed (24 killed, 7 equivalent) | `mutation/SURVIVORS.md` |
| 5 CI gate and PRs | week 2 | **Ahead**: gate workflow (PR #1), required on `team/sqe-tests`; blocked PR #37; DEF-01 fix PR #38 merged | `.github/workflows/sqe-quality-gate.yml` |
| 6–7 API tests, OpenAPI, generator | done | **Done**: 127 tests (113 pass, 14 pinned weaknesses); 58 generated cases; constraint change shown | `api/` |
| 8 Use cases + Playwright | done | **Done**: 6 use cases, 32 flows, all automated and passing | `e2e/` |
| 9 Usability and accessibility | done | **Done**: 2 task tests, scans before/after, one screen fixed | `a11y/` |
| 10 Security | done | **Done**: 13 access decisions, 5 controls, ZAP, pip-audit | `security/` |
| 11 Performance and recovery | done | **Done**: 4 k6 runs within limits; R1, R2 pass | `perf/` |
| 12 Test management | week 2 | **Ahead**: plan, risks, estimates, traceability, defect log, RCA drafted 18 Nov | `management/` |
| 13 Report, AI record, viva | week 3 | Not started | – |

Of the 13 areas, 11 are done or ahead, 1 is drafted early and 1 is not
started. The public fork, the Issues (#2–#36) and the CI gate were done on
18 Nov. What still lags is **ownership in the history**: every commit so far
is under one member's name.

## 2. GQM

**Goal:** assess the quality of the two ticket workflows, from the point of
view of the release decision, so the team can recommend release or hold.

| Question | Metric | Value (18 Nov) | Reading in context |
|---|---|---|---|
| Q1 How defect-prone is the code under test? | Defect density, backend: defects rooted in Python code / Python KLOC | 15 / 13.9 = **1.08 per KLOC** | Most backend defects come from the targeted tests, not a uniform sweep, so this is a lower bound for the app and not comparable to industry averages. |
| | Defect density, `hd_ticket.py` | 5 / 1.25 = **4.0 per KLOC** | The file that holds BR1–BR3 and assignment is about four times as defect-dense as the backend average. It is also Sonar's most complex file (cyclomatic 298). That supports putting the High risks there. |
| Q2 How completely are the requirements tested? | Requirements coverage, tested | 14 / 14 = **100 %** | Every requirement and rule has tests at two or more levels. |
| | Requirements coverage, passing | 14 / 14 = **100 %** (64 % on the baseline, 86 % after PR #38) | The DEF-01 fix (PR #38) moved FR-B6, BR1 and BR3 to passing, the DEF-02/03 fix (PR #41) FR-A4 and FR-B1. Minor defects remain open on several rows. |
| Q3 Are fixes holding? | Reopen rate: reopenings / fixed defects | 0 / 6 = **0 %** | Six fixes so far: DEF-01, DEF-02, DEF-03 and DEF-14 through the CI gate, and two accessibility fixes re-scanned locally. Every CI run since re-tests the gated fixes; the rate still says little after one day. |

Supporting figures: 34 defects counted (9 Major, 17 Minor, 8 Trivial), 28
open (4 Major, all accessibility); Pareto: accessibility 29 %, then business
rule, error handling and usability at 12 % each. By count, accessibility
dominates, partly because each axe rule is logged separately. By severity,
the Majors that blocked release were in business rules, access control and
a vulnerable library; all four are now fixed.

## 3. Deviations from the plan

| Deviation | Cause | Effect |
|---|---|---|
| SonarQube moved from week 2 to week 1 | Ready earlier | None; frees week 2 |
| Test management drafted in week 1 | Needed to steer the remaining work | Estimates for done areas are not blind (stated in `ESTIMATION.md`) |
| Environment problems: Playwright upgrade, missing RediSearch, port clash between Sonar and Frappe realtime | PJ-01 | About half a day lost in total (team to confirm from their logs) |
| All commits under one member's name | The area commits were made from one machine and account; the CI and fix PRs too | Commit history (a viva check) does not yet show who did what (PJ-03) |
| CI, Issues and the DEF-01, DEF-02, DEF-03 and DEF-14 fixes done in week 1 | Fork available on 18 Nov | Week 2 frees up for members' own checks and commits and the accessibility fix PR |
| DEF-03 fix breaks one upstream test | Upstream `test_non_agent_flow` asserts that tickets can be assigned to a portal user | Decided "agents only"; documented in RCA-2 and the completion report |
| A new defect, DEF-35, found by CI | UC-05 tests failed at random on the slower runner | Tests now fix the response order; DEF-35 pinned and filed as #36 |

## 4. Control actions for week 2

| # | Action | Owner | Due | Addresses |
|---|---|---|---|---|
| 1 | Create the public fork; each member commits their own area from `tests/team/` (one commit series per area, own name) | All | 23 Nov | PJ-03, PJ-04 |
| 2 | ~~File the defect log as GitHub Issues~~ done 18 Nov (#2–#36); still to do: triage them together in a short meeting | All | 24 Nov | defect management |
| 3 | ~~Build the CI pipeline; blocked PR; fix PR for DEF-01~~ done 18 Nov (PR #1, #37, #38); the member who owns CI must be able to explain the workflow and both PRs | M1 | 27 Nov | PJ-04, PR-02, EC-2 |
| 4 | ~~Fix PR for DEF-02 / DEF-03; rerun the access matrix~~ done 18 Nov (PR #41, 13 / 13 decisions); still to do: the RCA-2 preventive test (every whitelisted method × role) | M2, M3 | 28 Nov | PR-05, EC-3 |
| 5 | Each member starts a time log and fills Actual for their areas | All | ongoing | estimation comparison |
| 6 | Each member reruns one of their tests and explains the assertions to the others | All | 29 Nov | PJ-03 (viva) |
| 7 | Start the AI-use record from the prompts kept so far | All | 29 Nov | PJ-03 |
