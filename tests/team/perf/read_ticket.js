// k6 workload: an agent opens tickets (helpdesk...hd_ticket.api.get_one).
// This is the read behind every ticket page in both workflows.
//
//   k6 run -e VUS=1 -e OUT=result.json read_ticket.js
//
// Limits were fixed before the first run (see PERFORMANCE_REPORT.md):
//   1 user:  p95 <= 300 ms,  unexpected failures < 1 %
//   5 users: p95 <= 800 ms,  unexpected failures < 1 %
// Each run has a 10 s warm-up, then 60 s measured with every user active.
// Only the measured phase is reported.
import http from "k6/http";
import { check, fail, sleep } from "k6";
import { Rate } from "k6/metrics";

const BASE = __ENV.BASE || "http://127.0.0.1:8000";
const VUS = Number(__ENV.VUS || 1);
const P95_LIMIT_MS = Number(__ENV.P95_MS || (VUS > 1 ? 800 : 300));
const FAILURE_LIMIT = 0.01;
const TICKETS = Number(__ENV.TICKETS || 20);
const THINK_SECONDS = 0.5; // an agent glancing at a ticket before the next one
const ONE = `${BASE}/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.get_one`;

const unexpected = new Rate("unexpected_failures");

export const options = {
  scenarios: {
    warmup: {
      executor: "constant-vus", vus: VUS, duration: "10s", gracefulStop: "0s",
      exec: "openTicket", tags: { phase: "warmup" },
    },
    measured: {
      executor: "constant-vus", vus: VUS, duration: "60s", startTime: "10s", gracefulStop: "5s",
      exec: "openTicket", tags: { phase: "measured" },
    },
  },
  thresholds: {
    "http_req_duration{phase:measured}": [`p(95)<=${P95_LIMIT_MS}`],
    "unexpected_failures{phase:measured}": [`rate<${FAILURE_LIMIT}`],
    // listed so the measured-phase counts appear in the summary
    "http_reqs{phase:measured}": ["count>0"],
    "http_req_failed{phase:measured}": ["rate>=0"],
  },
  summaryTrendStats: ["avg", "min", "med", "p(90)", "p(95)", "p(99)", "max"],
};

function login(email, password) {
  const res = http.post(`${BASE}/api/method/login`, JSON.stringify({ usr: email, pwd: password }), {
    headers: { "Content-Type": "application/json" },
  });
  if (res.status !== 200) fail(`login failed for ${email}: HTTP ${res.status}`);
  return res.cookies.sid[0].value;
}

// Same starting data every run: the runner resets the site, then this creates
// TICKETS tickets as the customer and logs the agent in.
export function setup() {
  const customer = login(__ENV.CUSTOMER_EMAIL, __ENV.CUSTOMER_PASSWORD);
  const tickets = [];
  for (let i = 0; i < TICKETS; i++) {
    const res = http.post(
      `${BASE}/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.new`,
      JSON.stringify({ doc: { subject: `Load test ticket ${i + 1}`, description: `<p>Load test body ${i + 1}</p>` } }),
      { headers: { "Content-Type": "application/json", Cookie: `sid=${customer}` } }
    );
    if (res.status !== 200) fail(`could not create ticket ${i + 1}: HTTP ${res.status}`);
    tickets.push(res.json("message.name"));
  }
  return { agent: login(__ENV.AGENT_EMAIL, __ENV.AGENT_PASSWORD), tickets };
}

export function openTicket(data) {
  const ticket = data.tickets[(__VU * 7 + __ITER) % data.tickets.length];
  const res = http.get(`${ONE}?name=${ticket}`, {
    headers: { Cookie: `sid=${data.agent}`, Accept: "application/json" },
    tags: { name: "get_one" },
  });
  let ok = res.status === 200;
  if (ok) {
    try {
      ok = res.json("message.name") === ticket;
    } catch (e) {
      ok = false;
    }
  }
  unexpected.add(!ok);
  check(res, { "ticket returned": () => ok });
  sleep(THINK_SECONDS);
}

function metric(data, name, field) {
  const m = data.metrics[name];
  return m ? m.values[field] : null;
}

export function handleSummary(data) {
  const count = metric(data, "http_reqs{phase:measured}", "count");
  const result = {
    vus: VUS,
    run: __ENV.RUN || "1",
    limits: { p95_ms: P95_LIMIT_MS, unexpected_failure_rate: FAILURE_LIMIT },
    measured_seconds: 60,
    requests: count,
    requests_per_second: count / 60,
    p95_ms: metric(data, "http_req_duration{phase:measured}", "p(95)"),
    median_ms: metric(data, "http_req_duration{phase:measured}", "med"),
    max_ms: metric(data, "http_req_duration{phase:measured}", "max"),
    unexpected_failure_rate: metric(data, "unexpected_failures{phase:measured}", "rate"),
    http_failed_rate: metric(data, "http_req_failed{phase:measured}", "rate"),
    thresholds_passed: Object.values(data.metrics)
      .filter((m) => m.thresholds)
      .every((m) => Object.values(m.thresholds).every((t) => t.ok)),
  };
  const line =
    `VUs ${VUS} run ${result.run}: ${count} requests, ${result.requests_per_second.toFixed(1)} req/s, ` +
    `p95 ${result.p95_ms.toFixed(1)} ms (limit ${P95_LIMIT_MS}), ` +
    `unexpected failures ${(result.unexpected_failure_rate * 100).toFixed(2)} % (limit 1 %) -> ` +
    `${result.thresholds_passed ? "within limits" : "LIMIT EXCEEDED"}\n`;
  const out = {};
  out.stdout = line;
  if (__ENV.OUT) {
    out[__ENV.OUT] = JSON.stringify({ result, k6_summary: data }, null, 2);
  }
  return out;
}
