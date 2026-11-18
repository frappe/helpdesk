# Performance and recovery

## 1. Operation and limits (set before the first run)

**Operation:** an agent opens a ticket,
`GET /api/method/helpdesk.helpdesk.doctype.hd_ticket.api.get_one?name=<id>`.
It is the read behind every ticket page in both workflows (UC-02, UC-03,
UC-04, UC-05): the customer's page and the agent's page both load the ticket,
its conversation and its contact through it. It checks permissions, so it
exercises the same rules as the functional tests.

| Workload | p95 response-time limit | Unexpected-failure limit |
|---|---|---|
| 1 user | ≤ 300 ms | < 1 % of requests |
| 5 users at the same time | ≤ 800 ms | < 1 % of requests |

Why these limits:

* Opening a ticket fires about ten requests; `get_one` is the largest. For the
  page to feel immediate (about one second, the usual limit for keeping a
  user's flow of thought), this call should take at most a third of that for
  a single user, leaving room for the others: 300 ms.
* Five agents working at once is a realistic morning peak for a small team
  on one server. Some queueing is acceptable, but the page must still load
  within about a second: 800 ms for this call.
* A read of an existing ticket has no business reason to fail. Any non-200
  answer, or a 200 that does not contain the requested ticket, counts as an
  unexpected failure. 1 % tolerates a rare transient error, but a whole
  minute of measurement has 100+ requests, so even two failures at one user
  would breach it.

## 2. Method

* Tool: Grafana k6 OSS v2.4.0, one script (`perf/read_ticket.js`), run by
  `perf/run_load.sh`.
* Each run: reset the site to the seeded state, create the same 20 tickets as
  the customer, log the agent in, then a **10 s warm-up** and **60 s
  measured** with all users active from the start of the measured phase.
  Only the measured phase is reported (k6 tag `phase:measured`).
* Each user opens a ticket, then pauses 0.5 s (glancing at it) before the
  next. With a fixed pause, requests per second mainly reflects the number
  of users; the response time is what shows contention.
* Each setup ran twice; same build, machine and starting data. The limits
  are encoded as k6 thresholds, so k6 exits with 99 if one is crossed.

Environment (`perf/evidence/environment.txt`):

| | |
|---|---|
| Machine | Intel Core i5-13420H, 12 logical CPUs, 7.6 GB RAM, Windows 11 + WSL2 |
| OS | Ubuntu 26.04.1 LTS, kernel 6.18.58.1-microsoft-standard-WSL2 |
| Server | `bench serve --port 8000` (Werkzeug development server), one site, developer mode on |
| Versions | frappe v16.56.0 (49789a1), helpdesk e326986 (baseline + the team's uncommitted frontend accessibility fix, which does not touch this endpoint), Python 3.14.4, MariaDB 11.8.6, Redis 8.0.5 |
| Load generator | k6 on the same machine as the server |

## 3. Results

| Users | Run | Requests (60 s) | Requests/s | Median ms | p95 ms | p95 limit | Unexpected failures | Within limits |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 117 | 1.9 | 12.5 | 16.1 | 300 | 0.00 % | yes |
| 1 | 2 | 117 | 1.9 | 12.4 | 17.5 | 300 | 0.00 % | yes |
| 5 | 1 | 582 | 9.7 | 16.8 | 27.7 | 800 | 0.00 % | yes |
| 5 | 2 | 582 | 9.7 | 16.6 | 25.8 | 800 | 0.00 % | yes |

Raw output: `perf/evidence/vus*_run*.log` (console),
`vus*_run*.json` (k6 summary with the extracted result),
`vus*_run*.raw.json.gz` (every request as recorded by k6 `--out json`).

## 4. Interpretation against the targets

* **All four runs meet both limits by a wide margin**: p95 is about 6 % of
  the single-user limit and about 3 % of the five-user limit, with no
  unexpected failures in 1,398 measured requests.
* **The runs are comparable**: identical request counts, and p95 differs by
  1.4 ms (1 user) and 1.9 ms (5 users) between the two runs of a setup.
* **Effect of concurrency**: five users send five times the requests (1.9 to
  9.7 per second, as expected with a fixed pause), and p95 rises by about
  60 % (16.8 to 26.8 ms on average), median by about 35 %. The single
  development-server process starts to queue requests, but at this load it is
  far from saturated.
* **What the margin means**: the limits were chosen from the user's point of
  view, not from expected server speed. The headroom shows this operation is
  not the bottleneck for a small team. It does *not* show how many agents the
  server can carry; that needs a stress run without the pause, which was
  not part of this assessment.
* **Proposed regression gate** (for the CI and the risk register): p95 ≤ 100
  ms at 5 users, about four times the measured value, so a real slowdown
  (for example a permission check that starts querying per ticket) is caught
  while normal noise is not.

Limitations: development server, not gunicorn behind nginx; load generator
on the same machine; 20 small tickets; one operation measured.

## 5. Controlled failure and recovery

`api/test_failure_recovery.py` (pytest, run with the API suite). A test
double makes a dependency unavailable **after** the row is written inside the
transaction and **before** the commit. The test rolls back, as Frappe's
request handler does on any exception, checks what was persisted, restores
the dependency, retries the same request, and checks the final state.

| | R1: raise a ticket (workflow A) | R2: resolve a ticket (workflow B) |
|---|---|---|
| Dependency made unavailable | file storage, while the description's inline media are attached (`HDTicket.handle_inline_media_new_ticket`, in `after_insert`) | telemetry client (`capture_event`, in `HDTicket.on_update`) |
| State inside the transaction when it fails | ticket row and its first message already inserted | status already updated to Resolved |
| Persisted after the failure | no ticket, no message with the request's marker | status still Open, no resolution date, no new history (Version) entry |
| After restoring and retrying | exactly 1 ticket and 1 message; the same ticket number is reused (no gap, no duplicate); customer reads it over HTTP as Open | status Resolved with a resolution date; exactly 1 new history entry; agent reads it over HTTP as Resolved |
| Result | pass | pass |

Negative check: with the rollback replaced by a commit (a handler that
keeps partial work), both tests fail (`assert 1 == 0` for the half-written
ticket, `'Resolved' == 'Open'` for the status), so the assertions do detect a
system that does not recover cleanly. The modified copy was deleted
afterwards.

Observation: realtime notifications (`publish_event`) are sent only after
the commit (`after_commit=True` in `helpdesk/utils.py`), so a Redis outage
cannot leave a half-written ticket; it can only cost the live update in other
browsers.

## How to rerun

```
cd ~/frappe-bench/apps/helpdesk
bash tests/team/perf/run_load.sh                       # about 6 minutes
~/frappe-bench/env/bin/python -m pytest tests/team/api/test_failure_recovery.py -v
```
