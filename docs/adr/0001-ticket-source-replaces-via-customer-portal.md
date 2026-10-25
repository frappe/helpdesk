# Ticket source replaces via_customer_portal

A ticket's channel was a yes/no `via_customer_portal`, which could not hold a third channel once WhatsApp arrived. We replaced it with a `source` Select (Email, Portal, WhatsApp) and dropped the old field rather than keeping it as a mirror, because a mirror only protects reads, gives two answers to one question, and never gets removed. Existing tickets are backfilled by the column default (Email) plus one bulk update for portal tickets, with a second update for blanks as a safety net.

The WhatsApp option is added only when the whatsapp app (github.com/frappe/whatsapp) is installed (on `after_app_install` and `after_migrate`, since `install-app` never runs `after_migrate`) and is never removed on uninstall: Frappe re-validates Select values on every save, so removing it would make every existing WhatsApp ticket unsaveable.

## Consequences

- Custom reports or Server Scripts filtering on `via_customer_portal` break and must move to `source`; the upgrade note says so.
- Agent-raised tickets count as Portal, as they did before.
