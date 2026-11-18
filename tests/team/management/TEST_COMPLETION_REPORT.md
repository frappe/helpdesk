# Test completion report (interim, 18 Nov 2026)

> Interim version, written to make the release decision traceable now. It
> is final only after the week-2 fix PRs and the CI runs; update sections 4–6
> then.

## 1. Summary

The two ticket workflows of Frappe Helpdesk 16.1.0 (e326986) were tested at
unit, API, browser, usability/accessibility, security and performance
level. All 14 requirements and rules were tested. Three Major functional
or security defects are open, so **the recommendation is HOLD** until they
are fixed and regression-tested. The fixes are small and their tests already
exist as pinned expected failures.

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
| Static: SonarQube on 73 KLOC; cyclomatic complexity by hand | CI pipeline: **not yet built** |

## 3. Deviations from the plan

See `PROGRESS_WEEK1.md` §3. Main ones: CI and GitHub Issues not yet
started (fork pending); estimates for areas already done are not blind.

## 4. Open defects (18 Nov)

31 open of 33 counted: 8 Major, 16 Minor, 7 Trivial
(`generated/DEFECT_SUMMARY.md`). Those that bear on release:

| Defect | Severity | Risk | Release impact |
|---|---|---|---|
| DEF-01 auto-closed ticket has no resolution date | Major | PR-02, PR-03 | Blocks (RC-1) |
| DEF-02 customer can assign an agent | Major | PR-05 | Blocks (RC-2) |
| DEF-03 ticket can be assigned to, and read by, another customer | Major | PR-05 | Blocks (RC-2) |
| DEF-14 DOMPurify 3.4.8 with published CVEs | Major | PR-10 | Should fix before release (lock-file update) |
| DEF-17, -18, -19, -21 accessibility P1 issues on screens other than S2 | Major | PR-08 | Should fix; not a release criterion |

## 5. Residual risk per risk

| Risk | Inherent | Residual | Why |
|---|---|---|---|
| PR-01 BR2 feedback rule | 15 High | Low | MCC/MC/DC complete; mutants killed; only DEF-04 (minor) |
| PR-02 BR3 resolution date | 16 High | **High** | DEF-01 open |
| PR-03 BR1 boundary | 12 Medium | Medium | Boundary correct; DEF-01 side effect, DEF-11 |
| PR-04 BR4 customer lock | 12 Medium | Low | No defect |
| PR-05 access control | 15 High | **High** | DEF-02, DEF-03 open |
| PR-06 input / 5xx | 8 Medium | Medium | Several 5xx with tracebacks open |
| PR-07 duplicates / partial writes | 8 Medium | Low | Recovery verified; only DEF-10 (trivial) |
| PR-08 accessibility | 15 High | Medium | One screen fixed; P1 issues elsewhere |
| PR-09 performance | 6 Low | Low | 3 % of the p95 limit |
| PR-10 components | 12 Medium | Medium | DEF-14 open |
| PR-11 usability | 9 Medium | Medium | DEF-28, DEF-29 open |

## 6. Release criteria: actual against target

| Criterion | Target | Actual | Met? |
|---|---|---|---|
| RC-1 (EC-2) Open Major/Critical defects against BR1–BR4 | 0 | 1 (DEF-01) | **No** |
| RC-2 (EC-3) Access decisions as expected; open Major access-control defects | 13 / 13; 0 | 12 / 13; 2 | **No** |
| RC-3 (EC-4) p95 at 5 users; unexpected failures | ≤ 800 ms; < 1 % | 27.7 / 25.8 ms; 0 % | **Yes** |

Other exit criteria: EC-1 unit/coverage/mutation **met**; EC-5 fixed screen
accessibility **met**; EC-6 requirements traced **met**.

## 7. Recommendation

**HOLD.** Two of the three release criteria fail, both on the highest
risks (PR-02, PR-05). Change the recommendation to **RELEASE** when:

1. the fixes for DEF-01 and DEF-02/03 are merged through the CI gate;
2. the pinned tests (`test_auto_closed_ticket_…`, `test_customer_cannot_assign_an_agent`,
   `test_ticket_cannot_be_assigned_to_a_non_agent`, AC-08) pass and the full suites stay green;
3. RC-1 and RC-2 show 0 open Major defects.

DEF-14 (DOMPurify) should be fixed in the same cycle. The remaining minor
defects can be released with, and tracked as Issues.
