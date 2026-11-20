# The setup plan on the site

Keep the plan as one `Note`, so any later session, in any assistant, can read where the setup stands. A Note exists on every Frappe site and needs nothing installed.

- `title`: `Helpdesk setup plan`. One plan per site. Find it with `{"title": ["like", "Helpdesk setup plan%"]}`.
- `public`: 1. A Note that is not public is visible only to its owner, so nobody else, and no other session signed in as someone else, could read the plan.
- `content`: HTML, in the shape below. Write it in the person's language and words.

Read the whole Note before you change it, and write it back whole: `content` is one field. Show the edit and wait for a yes, as with every write.

## Shape

```html
<h3>About</h3>
<p><b>Business:</b> what they do, for whom, in one line.<br>
<b>Started:</b> 2026-11-16<br>
<b>Live means:</b> "Every customer email gets a reply within four working hours" (their words).<br>
<b>Live check:</b> no HD Ticket created in the last 7 days has first_response_failed_by above 0, with the SLA's response time at 4 working hours.<br>
<b>Set up by:</b> partner@example.com (setup users; leave empty when the business set itself up)</p>

<h3>Agreed</h3>
<ul>
<li>Ticket types: Order issue, Returns, Product question</li>
<li>Agents: 3 (names in the Agents step)</li>
<li>Working hours: Mon to Sat, 10:00 to 19:00; holidays: their 2026 list</li>
</ul>

<h3>Steps</h3>
<table>
<tr><th>#</th><th>Step</th><th>Why</th><th>Who</th><th>Status</th></tr>
<tr><td>1</td><td>Emails to support@ become tickets</td><td>All complaints arrive by email today</td><td>They connect, setup checks</td><td>Done 2026-11-16</td></tr>
<tr><td>2</td><td>Your three agents can sign in</td><td>Meera, Ali and Joe answer today</td><td>You invite, they sign in</td><td>To do</td></tr>
<tr><td>9</td><td>Your team answers a real ticket</td><td>The first sign the shared inbox is retired</td><td>Your team</td><td>To do</td></tr>
</table>

<h3>Asked for, not in this setup</h3>
<ul><li>2026-11-16: "Can tickets come from our WhatsApp number?"</li></ul>

<h3>Log</h3>
<p>Newest first. 2026-11-16: inbox connected. Agents next. The SLA waits for their holiday list.</p>
```

## Rules

- **Status** is `To do`, `Done <date>` or `Not needed: <reason>`. Mark a step done only after its Done when check passed on the data.
- **Who** is one of: Setup (you, or whoever sets up), They connect and setup checks, You invite and they sign in, You and they (they send, you import), Your team.
- Put the agreed values under "Agreed". The checks in `steps.md` compare the site against them.
- Never put a password, key or personal data beyond names and work emails in the Note. Every desk user can read it.
- When the plan changes after a session, change the steps and add a log line saying why.
