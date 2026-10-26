# Ticket source replaces via_customer_portal

A ticket's channel was a yes/no `via_customer_portal`, which could not hold a third channel once WhatsApp arrived. We replaced it with a `source` Select (Email, Portal, WhatsApp) and dropped the old field rather than keeping it as a mirror, because a mirror only protects reads, gives two answers to one question, and never gets removed. Existing tickets are backfilled by the column default (Email) plus one bulk update for portal tickets, with a second update for blanks as a safety net. Saved ticket views that filter or sort on the old field are rewritten to `source`, because a filter on a dropped field throws when the view opens. SLA and HD Ticket Assignment Rule conditions built on it are rewritten too, because the old name evaluates to nothing there and silently stops matching.

The WhatsApp option is added only when the whatsapp app (github.com/frappe/whatsapp) is installed (on `after_app_install` and `after_migrate`, since `install-app` never runs `after_migrate`) and is never removed on uninstall: Frappe re-validates Select values on every save, so removing it would make every existing WhatsApp ticket unsaveable.

## Consequences

- Custom reports, Server Scripts and hand-written conditions comparing `via_customer_portal` to a value break and must move to `source`; the upgrade note says so.
- Agent-raised tickets count as Portal, as they did before.
