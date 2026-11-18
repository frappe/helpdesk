| id | role | action | route | expected | observed | evidence |
|---|---|---|---|---|---|---|
| AC-01 | customerA | raise a ticket | POST /api/method/helpdesk.helpdesk.doctype.hd_ticket.api.new | allowed | allowed | HTTP 200 |
| AC-02 | customerA | read own ticket | GET /api/method/helpdesk.helpdesk.doctype.hd_ticket.api.get_one | allowed | allowed | HTTP 200 |
| AC-03 | customerB | read another customer's ticket | GET /helpdesk/my-tickets/1520; GET /api/method/helpdesk.helpdesk.doctype.hd_ticket.api.get_one | denied | denied | screen: "Not allowed via controller permission check", sent back to own list (screens/AC-03_customer_b_other_ticket.png); HTTP 403 PermissionError: Not allowed via controller permission check |
| AC-04 | customerA | set status to Resolved | PUT /api/resource/HD Ticket/1521 | denied | denied | HTTP 403 PermissionError: You cannot change Status after the ticket is raised; stored status Open |
| AC-05 | customerA | change priority | PUT /api/resource/HD Ticket/1522 | denied | denied | HTTP 403 PermissionError: You do not have permission to change Priority; stored priority Medium |
| AC-06 | customerA | open the agent ticket screen | GET /helpdesk/tickets/1523 | denied | denied | landed on /helpdesk/my-tickets/1523; agent controls shown: 0 (screens/AC-06_customer_agent_desk.png) |
| AC-07 | customerA | open the back-office ticket list | GET /app/hd-ticket | denied | denied | HTTP 403, landed on /desk/hd-ticket (screens/AC-07_customer_back_office.png) |
| AC-08 | customerA | assign an agent to own ticket | POST /api/method/run_doc_method (assign_agent) | denied | allowed | HTTP 200; assignees ["agent.one@sqe.test"] |
| AC-09 | agent | read a customer's ticket | GET /api/method/helpdesk.helpdesk.doctype.hd_ticket.api.get_one | allowed | allowed | HTTP 200 |
| AC-10 | agent | set status to Resolved | PUT /api/resource/HD Ticket/1526 | allowed | allowed | HTTP 200; stored status Resolved |
| AC-11 | agent | assign an agent | POST /api/method/run_doc_method (assign_agent) | allowed | allowed | HTTP 200; assignees ["agent.one@sqe.test"] |
| AC-12 | agent | delete a ticket | DELETE /api/resource/HD Ticket/1528 | denied | denied | HTTP 403 PermissionError: User agent.one@sqe.test does not have doctype access via role permission for document HD Ticket; ticket still stored: true |
| AC-13 | anonymous | read a ticket | GET /api/method/helpdesk.helpdesk.doctype.hd_ticket.api.get_one | denied | denied | HTTP 403 PermissionError: You are not permitted to access this resource. Login to accessFunction helpdesk.helpdesk.doctype.hd_ticket.api.get_one is not whitelisted. |
