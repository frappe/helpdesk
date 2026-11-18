# ZAP passive scan summary

Messages proxied: 7535. Distinct URLs seen: 293. Alert instances: 743.

| Risk | Alert | Plugin | CWE | Confidence | Instances | Routes (sample) | Evidence (sample) |
|---|---|---|---|---|---|---|---|
| High | Vulnerable JS Library | 10003 | 1395 | Medium | 1 | /assets/... | /*! @license DOMPurify 3.4.8 |
| Medium | Content Security Policy (CSP) Header Not Set | 10038 | 693 | High | 32 | /assets/..., /desk/hd-ticket, /helpdesk/my-tickets, /helpdesk/my-tickets/new (+4) |  |
| Medium | Missing Anti-clickjacking Header | 10020 | 1021 | Medium | 31 | /assets/..., /helpdesk/my-tickets, /helpdesk/my-tickets/new, /helpdesk/my-tickets/{id} (+3) | param x-frame-options |
| Medium | Sub Resource Integrity Attribute Missing | 90003 | 345 | High | 1 | /assets/... | <link rel="stylesheet" href="${x.value}" /> |
| Low | Application Error Disclosure | 90022 | 550 | Medium | 1 | /api/method/helpdesk.api.article.search | HTTP/1.1 500 INTERNAL SERVER ERROR |
| Low | Cookie No HttpOnly Flag | 10010 | 1004 | Medium | 20 | /api/method/helpdesk.api.doc.get_list_data, /api/method/helpdesk.helpdesk.doctype.hd_ticket.api.get_one, /api/method/login, /api/method/logout (+2) | param full_name; param system_user; param user_id |
| Low | Server Leaks Version Information via "Server" HTTP Response Header Field | 10036 | 497 | High | 302 | /api/method/frappe.apps.get_apps, /api/method/frappe.client.get, /api/method/frappe.client.get_count, /api/method/frappe.client.get_list (+46) | Werkzeug/3.1.9 Python/3.14.4 |
| Low | Timestamp Disclosure - Unix | 10096 | 497 | Low | 23 | /assets/..., /desk/hd-ticket, /login | 1502002290; 1530992060; 1560198380 |
| Low | X-Content-Type-Options Header Missing | 10021 | 693 | Medium | 295 | /api/method/frappe.apps.get_apps, /api/method/frappe.client.get, /api/method/frappe.client.get_count, /api/method/frappe.client.get_list (+43) | param x-content-type-options |
| Informational | Information Disclosure - Sensitive Information in URL | 10024 | 598 | Medium | 1 | /api/method/helpdesk.helpdesk.doctype.hd_ticket.api.get_ticket_assignees | param ticket |
| Informational | Information Disclosure - Suspicious Comments | 10027 | 615 | Medium | 5 | /assets/..., /login |  OTHERWISE, ARISING FROM,
 * OUT OF OR IN CO;  or not, to prevent username enumeration (CWE-20; // sfc-script:/home/administrator/frappe-bench/apps/f |
| Informational | Modern Web Application | 10109 | -1 | Medium | 31 | /assets/..., /helpdesk/my-tickets, /helpdesk/my-tickets/new, /helpdesk/my-tickets/{id} (+3) | <a href="#" class="btn-resend-link text-base-semibold text-ink-gray-6">Resend</a; <script type="module" crossorigin src="/assets/helpdesk/desk/assets/index-BFjH0w |

## Routes observed (excluding static assets)

- ``
- `/api`
- `/api/method`
- `/api/method/frappe.apps.get_apps`
- `/api/method/frappe.client.get`
- `/api/method/frappe.client.get_count`
- `/api/method/frappe.client.get_list`
- `/api/method/frappe.client.set_value`
- `/api/method/frappe.desk.form.activity.get_activity_timeline`
- `/api/method/frappe.desk.form.assign_to.add`
- `/api/method/frappe.desk.form.load.getdoctype`
- `/api/method/frappe.desk.search.search_link`
- `/api/method/frappe.onboarding.get_onboarding_status`
- `/api/method/frappe.utils.telemetry.pulse.client.boot_config`
- `/api/method/helpdesk.api.article.search`
- `/api/method/helpdesk.api.auth.get_current_user_email_info`
- `/api/method/helpdesk.api.auth.get_user`
- `/api/method/helpdesk.api.banners.get_banners`
- `/api/method/helpdesk.api.config.get_config`
- `/api/method/helpdesk.api.contact.search_contacts`
- `/api/method/helpdesk.api.doc.get_filterable_fields`
- `/api/method/helpdesk.api.doc.get_list_data`
- `/api/method/helpdesk.api.doc.get_quick_filters`
- `/api/method/helpdesk.api.doc.sort_options`
- `/api/method/helpdesk.api.general.get_translations`
- `/api/method/helpdesk.api.session.get_users`
- `/api/method/helpdesk.api.timeline.get_comment_extras`
- `/api/method/helpdesk.api.timeline.get_ticket_calls`
- `/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.get_navigation_tickets`
- `/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.get_one`
- `/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.get_recent_similar_tickets`
- `/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.get_ticket_assignees`
- `/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.get_ticket_contact`
- `/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.get_ticket_customizations`
- `/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.new`
- `/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.show_outside_hours_banner`
- `/api/method/helpdesk.helpdesk.doctype.hd_ticket_template.api.get_one`
- `/api/method/login`
- `/api/method/logout`
- `/api/method/run_doc_method`
- `/api/method/telephony.api.is_call_integration_enabled`
- `/api/resource`
- `/api/resource/HD%20Ticket`
- `/api/resource/HD%20Ticket/{id}`
- `/app`
- `/app/hd-ticket`
- `/assets`
- `/desk`
- `/desk/hd-ticket`
- `/helpdesk`
- `/helpdesk/my-tickets`
- `/helpdesk/my-tickets/new`
- `/helpdesk/my-tickets/{id}`
- `/helpdesk/tickets`
- `/helpdesk/tickets/{id}`
- `/login`
- `/website_script.js`
