# Test completion report (interim, 18 Nov 2026)

> Interim version, written to make the release decision traceable now. It
> becomes final after the week-3 regression run, the members' own checks
> (`ai/AI_USE_RECORD.md` §8) and the actual-effort figures.

## 1. Summary

The two ticket workflows of Frappe Helpdesk 16.1.0 (e326986) were tested at
unit, API, browser, usability/accessibility, security and performance
level, and every change now goes through a CI quality gate on the group's
fork. All 14 requirements and rules were tested, and all 14 now pass.

The three Major functional or security defects behind the earlier HOLD are
fixed and were re-tested through the gate:

- DEF-01 by PR #38;
- DEF-02 and DEF-03 by PR #41.

DEF-14, the bundled sanitiser library with published CVEs (Major), was the
main condition attached to release. It is fixed by PR #42. All three release
criteria are met, so **the recommendation is RELEASE, with the remaining
conditions in section 7**.

## 2. What was tested and what was not

| Tested | Not tested (and why) |
|---|---|
| FR-A1…A4, FR-B1…B6, BR1–BR4 (`TRACEABILITY.md`) | Email channel and email-to-ticket (out of scope) |
| Unit: 167 tests, 100 % statement and branch coverage of the rule scope; MCC + MC/DC on BR2; decision table on assignment | SLA computation beyond what the rules touch (out of scope) |
| Mutation: 238 mutants, 97.1 % | Upstream test suites (not counted, per the brief; used only as a regression check for the fixes) |
| API: 127 tests incl. 58 generated EP/BVA cases, repeated requests, recovery R1/R2 | Production stack: nginx, gunicorn, HTTPS; Secure cookie and HSTS observed only in the config template |
| Browser: 33 use-case flows (one pins DEF-35), 2 usability tasks incl. keyboard | Browsers other than Chromium; mobile layouts |
| Accessibility: axe + Lighthouse on 5 screens, before/after on 1 | Manual screen-reader testing (not required) |
| Security: 13 access decisions, 6 automated controls (CT-08 added with the DEF-14 fix), ZAP passive before and after the DEF-14 fix, pip-audit (178 packages) | Active scanning and penetration (out of scope by the brief) |
| Performance: k6 1 and 5 users, twice each | Stress or soak testing; capacity limits |
| Static: SonarQube on 73 KLOC; cyclomatic complexity by hand | |
| CI: GitHub Actions gate (unit + coverage, mutation, SonarQube, API + browser on a live site) on every PR into `team/sqe-tests`; required by branch protection. Blocked PR #37 (deliberate BR3 regression); fix PRs #38 (DEF-01), #41 (DEF-02/03), #42 (DEF-14) and #43 (accessibility, customer ticket screen) green and merged | k6, ZAP and Lighthouse/axe in CI (thresholds not meaningful on shared runners; run locally) |

## 3. Deviations from the plan

See `PROGRESS_WEEK1.md` §3. The main ones:

- Estimates for areas already done are not blind.
- CI, the GitHub Issues and the fixes for DEF-01/02/03 and DEF-14 were done
  on 18 Nov, ahead of the week-2 plan.
- The commit history does not yet show each member's own work (PJ-03).
- The DEF-03 fix makes one upstream test fail on purpose (section 7).

## 4. Open defects (18 Nov)

28 open of 34 counted: 4 Major, 17 Minor, 7 Trivial
(`generated/DEFECT_SUMMARY.md`; GitHub Issues #2–#36). DEF-01, DEF-02,
DEF-03 and DEF-14 are closed. Those that bear on release:

| Defect | Severity | Risk | Release impact |
|---|---|---|---|
| DEF-01 auto-closed ticket has no resolution date | Major | PR-02, PR-03 | **Closed** by PR #38; re-tested in CI |
| DEF-02 customer can assign an agent | Major | PR-05 | **Closed** by PR #41; re-tested in CI |
| DEF-03 ticket can be assigned to, and read by, another customer | Major | PR-05 | **Closed** by PR #41; re-tested in CI |
| DEF-14 DOMPurify 3.4.8 with published CVEs | Major | PR-10 | **Closed** by PR #42 (3.4.18); CT-08 and ZAP re-checked |
| DEF-17, -18, -19, -21 accessibility P1 issues on screens other than S2 | Major | PR-08 | Known issues; not a release criterion; next cycle |
| DEF-35 closed ticket shown as open when the status list loads late | Minor | PR-11 | Known issue; customer may be offered a message box on a closed ticket |

## 5. Residual risk per risk

| Risk | Inherent | Residual | Why |
|---|---|---|---|
| PR-01 BR2 feedback rule | 15 High | Low | MCC/MC/DC complete; mutants killed; only DEF-04 (minor) |
| PR-02 BR3 resolution date | 16 High | Low | DEF-01 fixed and re-tested; DEF-05 (minor) open; tickets closed by the job before the fix still need the RCA-1 data repair |
| PR-03 BR1 boundary | 12 Medium | Low | Boundary correct; DEF-01 fixed; DEF-11 (minor) open |
| PR-04 BR4 customer lock | 12 Medium | Low | No defect |
| PR-05 access control | 15 High | Low | DEF-02, DEF-03 fixed and re-tested; 13 / 13 access decisions as expected; the RCA-2 preventive test (every whitelisted method × role) is not yet written |
| PR-06 input / 5xx | 8 Medium | Medium | Several 5xx with tracebacks open |
| PR-07 duplicates / partial writes | 8 Medium | Low | Recovery verified; only DEF-10 (trivial) |
| PR-08 accessibility | 15 High | Medium | Customer ticket screen fixed (PR #43, re-scanned on the merged code base); P1 issues open on S1, S4, S5 (DEF-17/18/19/21) |
| PR-09 performance | 6 Low | Low | 3 % of the p95 limit |
| PR-10 components | 12 Medium | Low | DEF-14 fixed (PR #42); CT-08 now guards the served sanitiser version; DEF-15 (no CSP) and DEF-16 (accepted) remain; the JavaScript dependencies are only checked by ZAP's library list, not by a full audit |
| PR-11 usability | 9 Medium | Medium | DEF-28, DEF-29, DEF-35 open |

## 6. Release criteria: actual against target

| Criterion | Target | Actual | Met? |
|---|---|---|---|
| RC-1 (EC-2) Open Major/Critical defects against BR1–BR4 | 0 | 0 (DEF-01 closed by PR #38) | **Yes** |
| RC-2 (EC-3) Access decisions as expected; open Major access-control defects | 13 / 13; 0 | 13 / 13; 0 (DEF-02/03 closed by PR #41) | **Yes** |
| RC-3 (EC-4) p95 at 5 users; unexpected failures | ≤ 800 ms; < 1 % | 27.7 / 25.8 ms; 0 % | **Yes** |

Other exit criteria: EC-1 unit/coverage/mutation **met**; EC-5 fixed screen
accessibility **met**; EC-6 requirements traced **met**.

## 7. Recommendation

**RELEASE, with conditions.** All three release criteria are met. The
highest risks (PR-02 resolution date, PR-05 access control) went from High
to Low through fixes that were pinned by failing tests first, then merged
only after the required gate passed.

Conditions and known issues for the release notes:

1. ~~**DEF-14**: upgrade DOMPurify before deployment~~. Done in PR #42
   (3.4.18). The served bundle was checked by CT-08 and by ZAP: 0
   vulnerable-library alerts, against 1 on the baseline.
2. **Data repair (RCA-1)**: back-fill the resolution date of tickets the job
   closed before PR #38.
3. **Behaviour change (DEF-03)**: tickets can now be assigned only to agents.
   Upstream's `test_non_agent_flow`, which assigns a ticket to a portal user
   with no roles, fails by design. This needs to be stated if the fix is
   offered upstream.
4. **Known issues**: the accessibility P1 issues (DEF-17/18/19/21), DEF-35
   and the remaining minor defects are released with, and tracked as
   Issues.

If condition 2 cannot be met before deployment, the recommendation reverts
to HOLD for that reason.
