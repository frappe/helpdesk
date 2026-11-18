# Effort estimation (three-point)

Unit: person-hours for the whole team. **E = (O + 4M + P) / 6** (PERT),
**SD = (P − O) / 6**.

> Honesty note for the report: these estimates were written down on
> 2026-11-18, after much of week 1's work had already started, so they are
> not a blind forecast for those areas. Say so in the report. The **Actual**
> column must come from each member's own time log; it is left empty here
> on purpose and must not be filled with guesses.

| # | Area | Owner | O | M | P | E | SD | Actual | Variance (Actual − E) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Environment, baseline, scope and test basis | All | 4 | 8 | 16 | 8.7 | 2.0 | | |
| 2 | SonarQube and hand-calculated complexity | M1 | 3 | 5 | 10 | 5.5 | 1.2 | | |
| 3 | White-box unit tests, MCC and MC/DC | M1 | 8 | 14 | 24 | 14.7 | 2.7 | | |
| 4 | Mutation testing and survivor analysis | M1 | 4 | 8 | 14 | 8.3 | 1.7 | | |
| 5 | CI quality gate, blocked PR, fix PR | M1 | 6 | 10 | 20 | 11.0 | 2.3 | | |
| 6 | API and integration tests | M2 | 10 | 16 | 28 | 17.0 | 3.0 | | |
| 7 | OpenAPI spec, generator, constraint change | M2 | 5 | 8 | 14 | 8.5 | 1.5 | | |
| 8 | Use-case specification and Playwright automation | All | 10 | 16 | 30 | 17.3 | 3.3 | | |
| 9 | Usability and accessibility | M3 | 6 | 10 | 18 | 10.7 | 2.0 | | |
| 10 | Security assessment | M3 | 6 | 9 | 16 | 9.7 | 1.7 | | |
| 11 | Performance and recovery | M3 | 4 | 7 | 12 | 7.3 | 1.3 | | |
| 12 | Test management documents and defect management | All | 8 | 12 | 20 | 12.7 | 2.0 | | |
| 13 | Final report, AI-use record, viva preparation | All | 6 | 10 | 16 | 10.3 | 1.7 | | |
| | **Total** | | **80** | **133** | **238** | **141.7** | **7.6** | | |

Total SD is √(Σ SD²) = 7.6 h, so the team total is expected within about
**126–157 person-hours** (± 2 SD), roughly 47 hours per member.

Per member (sum of E for owned areas plus a third of shared areas):
M1 ≈ 39.5 + 16.3 = 55.8 h; M2 ≈ 25.5 + 16.3 = 41.8 h; M3 ≈ 27.7 + 16.3 = 44.0 h.
M1 carries the most; the team can rebalance by moving one of M1's use
cases (UC-02) to M2.

## How to complete the comparison

1. Each member keeps a simple log (date, area #, hours, what was done) from
   now on and reconstructs earlier days from commits and their own notes.
2. At the end, fill **Actual** per area and **Variance**; mark areas outside
   E ± 2 SD.
3. In the completion report, explain the largest variances (for example
   environment problems, PJ-01; AI assistance shortening some areas, which
   must also appear in the AI-use record).

Machine time is not effort, but these measured run times help explain
variances (from the junit and scanner logs): unit suite 2.0 s (159
tests), API suite 18.1 s (127 tests), security Playwright suite 21.5 s
(18 tests), SonarQube scan of the app 1 min 7 s, k6 set of four runs about
6 min.
