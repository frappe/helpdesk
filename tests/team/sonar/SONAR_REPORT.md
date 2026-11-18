# Static analysis with SonarQube

## 1. Set-up

| | |
|---|---|
| Server | SonarQube Community Build 26.11.0.134175, local (`~/sonar/sonarqube`, embedded H2 database, port 9100 because Frappe's realtime server uses 9000) |
| Scanner | SonarScanner CLI 8.4.0.16527 |
| Downloads | from binaries.sonarsource.com, SHA-256 checked against the published `.sha256` files |
| Code analysed | Helpdesk at baseline `e326986` (version-16), plus the team's uncommitted accessibility fix in five frontend files (see `a11y/evidence/fix.diff`) |
| Sources | `helpdesk/` (Python backend) and `desk/src/` (Vue/TypeScript frontend) |
| Excluded | `node_modules`, built assets (`helpdesk/public`), translations, `*.d.ts`, minified files; upstream test files are indexed as tests, not sources |
| Rules | default "Sonar way" profiles for every language |
| Coverage imported | `reports/unit/coverage.xml` and `junit.xml` from `run_unit.sh` (the unit suite, 159 tests) |
| Analysis date | 2026-11-18 01:13 (+05:00) |
| Configuration | `sonar/sonar-project.properties`; run by `sonar/run_sonar.sh` |

A second project, `helpdesk-complexity`, analyses only the three business-rule
files with a team profile ("SQE complexity probe") in which the function
cyclomatic complexity rule (S1541) and the cognitive complexity rule (S3776)
have their threshold lowered to 1. Sonar then reports the exact value of
every function, which its web UI does not otherwise show per function.

Raw output: `sonar/evidence/main/` and `sonar/evidence/complexity/`
(measures, per-file measures, issues, hotspots, gate status as JSON),
scanner logs, and the generated `sonar/evidence/summary.md`.

## 2. Whole application

| Metric | Value |
|---|---|
| Lines of code (ncloc) | 73,337 in 706 files (Python 13,935; JavaScript/Vue 48,960; TypeScript 10,224) |
| Functions | 4,491 (Python 862) |
| Cyclomatic complexity | 10,230 (Python 2,729) |
| Cognitive complexity | 6,226 (Python 2,447) |
| Duplicated lines | 1.6 % (36 blocks, 1,355 lines) |
| Comment density | 4.1 % |
| Bugs / vulnerabilities / code smells | 122 / 8 / 59 (189 issues) |
| Security hotspots | 0 |
| Ratings | reliability **D**, security **D**, maintainability **A**, security review **A** |
| Technical debt | 252 min (debt ratio 0.0 %) |
| Coverage (overall / Python only) | 1.7 % / 4.6 % |
| Unit tests imported | 159, 0 failures, 0 errors |
| Quality gate (Sonar way) | **Passed**, with no conditions evaluated (see 5) |

By language (from per-file measures):

| Language | Files | ncloc | Cyclomatic | Cognitive | Bugs | Vulnerabilities | Code smells |
|---|---|---|---|---|---|---|---|
| JavaScript / Vue | 375 | 48,960 | 5,510 | 2,493 | 81 | 4 | 33 |
| Python | 231 | 13,935 | 2,729 | 2,447 | 2 | 0 | 1 |
| TypeScript | 94 | 10,224 | 1,986 | 1,286 | 39 | 4 | 25 |

The most complex file is `hd_ticket.py` (1,250 ncloc, 81 functions,
cyclomatic 298, cognitive 252), the file that holds BR1–BR3. The next are
frontend utilities (`desk/src/utils.ts` 264, `tiptap-extensions.ts` 222).

## 3. The business-rule scope

| File | ncloc | Cyclomatic | Cognitive | Coverage (Sonar) |
|---|---|---|---|---|
| `hd_ticket/customer_edit_controller.py` (BR4) | 80 | 32 | 19 | 100 % |
| `hd_ticket_status/hd_ticket_status.py` (status rules) | 101 | 27 | 27 | 100 % |
| `hd_ticket/hd_ticket.py` (whole file) | 1,250 | 298 | 252 | 17.6 % |

| Function (rule) | Cyclomatic | Cognitive |
|---|---|---|
| `close_tickets_after_n_days` (BR1) | 5 (6 by hand) | 7 |
| `HDTicket.validate_feedback` (BR2) | 6 | 2 |
| `HDTicket.is_valid_status_transition` (BR3) | 5 | 4 |
| `HDTicket.set_resolution_date` (BR3) | 5 | 4 |
| `CustomerEditController.prevent_customer_edits` (BR4) | 13 | 8 |
| `CustomerEditController.check_update_perms` (BR4) | 6 | 5 |
| `HDTicketStatus.validate_disabling_status` | 11 | 14 |
| `HDTicketStatus.validate_required_categories` | 7 | 7 |
| `HDTicketStatus.validate_closed_status_change` | 6 | 5 |

The rule functions are small (5–13). For comparison, the most complex
functions in `hd_ticket.py` are outside the scope:
`reply_via_agent` 17 / 20, `set_customer` 13 / 14 and
`on_communication_update` 13 / 16. They would be the first candidates if
the scope grew.

Coverage: Sonar shows 17.6 % for `hd_ticket.py` because it measures the
whole file, while the unit suite targets only four functions in it. Measured
on the scope, coverage is 100 % statements (142) and 100 % branches (66)
(`tools/scoped_coverage.py`, `evidence/unit_run.txt`). The overall 1.7 % is
not a measure of the team's testing: the API, use-case and security suites
run against the live server, and their coverage is not collected.

The hand calculation and the comparison with Sonar are in
**`sonar/CYCLOMATIC_COMPLEXITY.md`**: `close_tickets_after_n_days` is 6 by
hand (CFG, decision count and regions) and 5 in Sonar, because Sonar's
Python analyser does not count `except` clauses. A calibration file proved
this; it also showed that Sonar does not count `elif`.

## 4. Issues and their triage

All 189 issues and their impacts (Sonar 26 classifies by software quality):

| Quality | Blocker | High | Medium | Low |
|---|---|---|---|---|
| Reliability | | 6 | 173 | |
| Security | | 4 | | 4 |
| Maintainability | 2 | 1 | 3 | 47 |

186 of the 189 are in the frontend. The most frequent rules: Vue emit
pattern (`typescript:S8951`, 44), promises neither awaited nor handled
(`S9383`, 42), `parseInt` instead of `Number.parseInt` (`S7773`, 37), inputs
without a label (`Web:InputWithoutLabelCheck`, 21 plus 5 `Web:S6853`).

Triage of every Python issue and every blocker/high issue:

| Finding | Location | Team verdict |
|---|---|---|
| Unreachable code (`python:S1763`, medium) | `helpdesk/api/knowledge_base.py:43` | **True positive**, harmless: a second `return article` after the function has already returned. Dead code. |
| Function always returns the same value (`python:S3516`, blocker) | `helpdesk/api/timeline.py:12` | **False positive**: `get_comment_extras` returns the same dict object on both paths, but `add_attachments`/`add_reactions` fill it in between. |
| Element accessed without checking it exists (`python:S8904`, high) | `hd_notification.py:38` | **True positive (latent defect)**: `img["src"]` raises `KeyError` if a notification's HTML has an `<img>` without `src`. Not reachable from the two workflows; logged as a minor finding, not tested further. |
| Dynamic code execution, `new Function` (`typescript:S1523`, 4 × high security) | `desk/src/composables/formCustomisation.ts:93–94, 201–202` | **By design, risk accepted**: runs form scripts and expressions that a System Manager writes in *HD Form Script*. Only privileged users can author them, so this is not exploitable by agents or customers. It is also why a strict CSP is not simple to add (SEC-03). |
| Missing `:key` on `v-for` (`typescript:S8982`/`S8984`, 5 × high reliability) | `SettingsModal.vue`, `TicketStats.vue`, `TicketContactTab.vue`, `TicketHeader.vue`, `TicketCustomerSidebar.vue` | **True positive**, low impact: lists may re-render wrongly when items change order. Not observed in the use-case runs. |
| Exported mutable `let` (`javascript:S6861`, high) | `desk/src/components/dialogs.jsx:6` | True positive, maintainability only. |
| Function always returns the same value (`typescript:S3516`, blocker) | `desk/src/tiptap-extensions.ts:799` | Not triaged further: editor plug-in outside the workflows. |

The two D ratings come from these frontend findings: security D from the
four `new Function` vulnerabilities, reliability D from the high
reliability findings. The Python backend, where the business rules live,
has no vulnerability, two minor true-positive bugs (dead code, unchecked
`src`) and one code smell, which is a false positive.

Sonar found **none** of the defects the dynamic tests found (D-01 auto-close
without a resolution date, SEC-01 customer can assign a ticket, the
W-API-02/03/09 server errors). They are logic and authorisation faults that
static rules cannot see, which is the argument for testing at several
levels.

## 5. Quality gate

The default "Sonar way" gate passed, but it only judges **new code**
(coverage ≥ 80 %, duplication ≤ 3 %, no new issues, all hotspots
reviewed). On a first analysis there is no new code, so no condition was
evaluated (`conditions: []` in `evidence/main/quality_gate.json`). The
repository is a shallow clone, so Sonar also had no blame information to
date lines.

The team gate for the CI pipeline (section on CI) will therefore be explicit
and scoped:

| Condition | Threshold | Source |
|---|---|---|
| Unit tests | all pass | junit |
| Scope statement and branch coverage | 100 % | `tools/scoped_coverage.py` |
| Mutation score on the scope | ≥ 95 % | `run_mutation.sh` |
| Sonar: new bugs / new vulnerabilities on new code | 0 | Sonar gate "SQE gate" |
| Sonar: coverage on new Python code | ≥ 80 % | Sonar gate |
| Sonar: duplication on new code | ≤ 3 % | Sonar gate |

## How to rerun

```
bash tests/team/sonar/server.sh start         # first time: python tests/team/sonar/sonar_admin.py init
bash tests/team/sonar/run_sonar.sh            # about 3 minutes
bash tests/team/sonar/calibration/run_calibration.sh
```

The admin password and analysis token are created by `sonar_admin.py init`
and kept in `~/.sqe-env` (not in the repository, never printed).
