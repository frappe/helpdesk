# Test completion report (interim, 18 Nov 2026)

> Interim version, written to make the release decision traceable now. It
> is final only after the week-2 fix PRs and the CI runs; update sections 4–6
> then.

## 1. Summary

The two ticket workflows of Frappe Helpdesk 16.1.0 (e326986) were tested at
unit, API, browser, usability/accessibility, security and performance
level, and every change now goes through a CI quality gate on the group's
fork. All 14 requirements and rules were tested. Of the three Major
functional or security defects found, DEF-01 is fixed (PR #38, merged
through the gate). The two access-control defects, DEF-02 and DEF-03, are
still open, so **the recommendation is HOLD** until they are fixed and
regression-tested. Their fix is small and its tests already exist as pinned
expected failures.

## 2. What was tested and what was not

| Tested | Not tested (and why) |
|---|---|
| FR-A1…A4, FR-B1…B6, BR1–BR4 (`TRACEABILITY.md`) | Email channel and email-to-ticket (out of scope) |
| Unit: 159 tests, 100 % statement and branch coverage of the rule scope; MCC + MC/DC on BR2 | SLA computation beyond what the rules touch (out of scope) |
| Mutation: 237 mutants, 97.0 % (100 % of killable) | Upstream test suites (not counted, per the brief) |
| API: 127 tests incl. 58 generated EP/BVA cases, repeated requests, recovery R1/R2 | Production stack: nginx, gunicorn, HTTPS; Secure cookie and HSTS observed only in the config template |
| Browser: 32 use-case flows, 2 usability tasks incl. keyboard | Browsers other than Chromium; mobile layouts |
| Accessibility: axe + Lighthouse on 5 screens, before/after on 1 | Manual screen-reader testing (not required) |
| Security: 13 access decisions, 5 controls, ZAP passive, pip-audit (178 packages) | Active scanning and penetration (out of scope by the brief) |
| Performance: k6 1 and 5 users, twice each | Stress or soak testing; capacity limits |
| Static: SonarQube on 73 KLOC; cyclomatic complexity by hand | |
| CI: GitHub Actions gate (unit + coverage, mutation, SonarQube, API + browser on a live site) on every PR into `team/sqe-tests`; required by branch protection. Blocked PR #37 (deliberate BR3 regression, caught by unit, API, mutation and Sonar jobs); fix PR #38 (DEF-01) green and merged | k6, ZAP and Lighthouse/axe in CI (thresholds not meaningful on shared runners; run locally) |

## 3. Deviations from the plan

See `PROGRESS_WEEK1.md` §3. Main ones: estimates for areas already done
are not blind; CI, GitHub Issues and the DEF-01 fix were done on 18 Nov,
ahead of the week-2 plan, but the commit history does not yet show each
member's own work (PJ-03).

## 4. Open defects (18 Nov)

31 open of 34 counted: 7 Major, 17 Minor, 7 Trivial
(`generated/DEFECT_SUMMARY.md`; GitHub Issues #2–#36). DEF-01 is closed.
DEF-35 (Minor) was found by the CI runs: on a slow load, a closed ticket is
shown to its customer as open. Those that bear on release:

| Defect | Severity | Risk | Release impact |
|---|---|---|---|
| DEF-01 auto-closed ticket has no resolution date | Major | PR-02, PR-03 | **Closed** by PR #38; re-tested in CI |
| DEF-02 customer can assign an agent | Major | PR-05 | Blocks (RC-2) |
| DEF-03 ticket can be assigned to, and read by, another customer | Major | PR-05 | Blocks (RC-2) |
| DEF-14 DOMPurify 3.4.8 with published CVEs | Major | PR-10 | Should fix before release (lock-file update) |
| DEF-17, -18, -19, -21 accessibility P1 issues on screens other than S2 | Major | PR-08 | Should fix; not a release criterion |

## 5. Residual risk per risk

| Risk | Inherent | Residual | Why |
|---|---|---|---|
| PR-01 BR2 feedback rule | 15 High | Low | MCC/MC/DC complete; mutants killed; only DEF-04 (minor) |
| PR-02 BR3 resolution date | 16 High | Low | DEF-01 fixed and re-tested; DEF-05 (minor) open; tickets closed by the job before the fix still need the RCA-1 data repair |
| PR-03 BR1 boundary | 12 Medium | Low | Boundary correct; DEF-01 fixed; DEF-11 (minor) open |
| PR-04 BR4 customer lock | 12 Medium | Low | No defect |
| PR-05 access control | 15 High | **High** | DEF-02, DEF-03 open |
| PR-06 input / 5xx | 8 Medium | Medium | Several 5xx with tracebacks open |
| PR-07 duplicates / partial writes | 8 Medium | Low | Recovery verified; only DEF-10 (trivial) |
| PR-08 accessibility | 15 High | Medium | One screen fixed; P1 issues elsewhere |
| PR-09 performance | 6 Low | Low | 3 % of the p95 limit |
| PR-10 components | 12 Medium | Medium | DEF-14 open |
| PR-11 usability | 9 Medium | Medium | DEF-28, DEF-29, DEF-35 open |

## 6. Release criteria: actual against target

| Criterion | Target | Actual | Met? |
|---|---|---|---|
| RC-1 (EC-2) Open Major/Critical defects against BR1–BR4 | 0 | 0 (DEF-01 closed by PR #38) | **Yes** |
| RC-2 (EC-3) Access decisions as expected; open Major access-control defects | 13 / 13; 0 | 12 / 13; 2 | **No** |
| RC-3 (EC-4) p95 at 5 users; unexpected failures | ≤ 800 ms; < 1 % | 27.7 / 25.8 ms; 0 % | **Yes** |

Other exit criteria: EC-1 unit/coverage/mutation **met**; EC-5 fixed screen
accessibility **met**; EC-6 requirements traced **met**.

## 7. Recommendation

**HOLD.** RC-1 and RC-3 are met. RC-2 fails on the highest remaining risk
(PR-05, access control). Change the recommendation to **RELEASE** when:

1. the fix for DEF-02/03 (RCA-2: `agent_only` plus a target check) is merged
   through the CI gate;
2. the pinned tests `test_customer_cannot_assign_an_agent`,
   `test_ticket_cannot_be_assigned_to_a_non_agent` and AC-08 pass, and the
   full suites stay green;
3. RC-2 shows 13 / 13 access decisions as expected and 0 open Major
   access-control defects.

DEF-01 already went through this path: pinned test, fix PR, green gate,
merge, Issue closed.

DEF-14 (DOMPurify) should be fixed in the same cycle. The remaining minor
defects can be released with, and tracked as Issues.
