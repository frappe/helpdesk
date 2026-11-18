# Mutation report

- Mutants in scope: 237
- Killed: 206
- Survived: 31
- Incompetent (not runnable): 0
- Abnormal / timeout: 0
- Skipped (outside scope): 746
- Still pending: 0
- **Mutation score: 86.9%** (killed / (killed + survived))

## By file

| File | Killed | Survived | Score |
|---|---|---|---|
| customer_edit_controller.py | 66 | 9 | 88.0% |
| hd_ticket.py | 72 | 10 | 87.8% |
| hd_ticket_status.py | 68 | 12 | 85.0% |

## By operator

| Operator | Killed | Survived |
|---|---|---|
| core/AddNot | 36 | 0 |
| core/ExceptionReplacer | 1 | 0 |
| core/NumberReplacer | 12 | 0 |
| core/ReplaceAndWithOr | 8 | 0 |
| core/ReplaceBinaryOperator_BitOr_Add | 1 | 0 |
| core/ReplaceBinaryOperator_BitOr_BitAnd | 1 | 0 |
| core/ReplaceBinaryOperator_BitOr_BitXor | 0 | 1 |
| core/ReplaceBinaryOperator_BitOr_Div | 1 | 0 |
| core/ReplaceBinaryOperator_BitOr_FloorDiv | 1 | 0 |
| core/ReplaceBinaryOperator_BitOr_LShift | 1 | 0 |
| core/ReplaceBinaryOperator_BitOr_Mod | 1 | 0 |
| core/ReplaceBinaryOperator_BitOr_Mul | 1 | 0 |
| core/ReplaceBinaryOperator_BitOr_Pow | 1 | 0 |
| core/ReplaceBinaryOperator_BitOr_RShift | 1 | 0 |
| core/ReplaceBinaryOperator_BitOr_Sub | 1 | 0 |
| core/ReplaceComparisonOperator_Eq_Gt | 9 | 0 |
| core/ReplaceComparisonOperator_Eq_GtE | 9 | 0 |
| core/ReplaceComparisonOperator_Eq_Is | 0 | 6 |
| core/ReplaceComparisonOperator_Eq_IsNot | 6 | 0 |
| core/ReplaceComparisonOperator_Eq_Lt | 9 | 0 |
| core/ReplaceComparisonOperator_Eq_LtE | 1 | 8 |
| core/ReplaceComparisonOperator_Eq_NotEq | 9 | 0 |
| core/ReplaceComparisonOperator_Gt_Eq | 1 | 0 |
| core/ReplaceComparisonOperator_Gt_GtE | 1 | 0 |
| core/ReplaceComparisonOperator_Gt_Lt | 1 | 0 |
| core/ReplaceComparisonOperator_Gt_LtE | 1 | 0 |
| core/ReplaceComparisonOperator_Gt_NotEq | 1 | 0 |
| core/ReplaceComparisonOperator_NotEq_Eq | 7 | 0 |
| core/ReplaceComparisonOperator_NotEq_Gt | 3 | 4 |
| core/ReplaceComparisonOperator_NotEq_GtE | 7 | 0 |
| core/ReplaceComparisonOperator_NotEq_Is | 7 | 0 |
| core/ReplaceComparisonOperator_NotEq_IsNot | 0 | 7 |
| core/ReplaceComparisonOperator_NotEq_Lt | 4 | 3 |
| core/ReplaceComparisonOperator_NotEq_LtE | 7 | 0 |
| core/ReplaceContinueWithBreak | 0 | 1 |
| core/ReplaceFalseWithTrue | 1 | 1 |
| core/ReplaceOrWithAnd | 16 | 0 |
| core/ReplaceTrueWithFalse | 3 | 0 |
| core/ReplaceUnaryOperator_Delete_Not | 13 | 0 |
| core/ReplaceUnaryOperator_Delete_USub | 1 | 0 |
| core/ReplaceUnaryOperator_USub_Invert | 1 | 0 |
| core/ReplaceUnaryOperator_USub_Not | 1 | 0 |
| core/ReplaceUnaryOperator_USub_UAdd | 1 | 0 |
| core/ZeroIterationForLoop | 1 | 0 |
| sqe/GrantAgentExemption | 4 | 0 |
| sqe/RevokeAgentExemption | 4 | 0 |
| sqe/SwapTicketStatus | 10 | 0 |

## Surviving mutants (31)

### S1. customer_edit_controller.py:23 — core/ReplaceComparisonOperator_NotEq_Gt (occurrence 0)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket/customer_edit_controller.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket/customer_edit_controller.py
@@ -20,7 +20,7 @@
         # a System Manager pulling emails is not the sender of the pulled tickets
         if is_agent() or "System Manager" in frappe.get_roles():
             return
-        if frappe.session.user != "Guest":
+        if frappe.session.user > "Guest":
             self.raised_by = frappe.session.user
         self.via_customer_portal = 1
         self.flags.ignore_permlevel_for_fields = [
```

### S2. customer_edit_controller.py:23 — core/ReplaceComparisonOperator_NotEq_IsNot (occurrence 0)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket/customer_edit_controller.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket/customer_edit_controller.py
@@ -20,7 +20,7 @@
         # a System Manager pulling emails is not the sender of the pulled tickets
         if is_agent() or "System Manager" in frappe.get_roles():
             return
-        if frappe.session.user != "Guest":
+        if frappe.session.user is not "Guest":
             self.raised_by = frappe.session.user
         self.via_customer_portal = 1
         self.flags.ignore_permlevel_for_fields = [
```

### S3. customer_edit_controller.py:39 — core/ReplaceComparisonOperator_Eq_Is (occurrence 0)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket/customer_edit_controller.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket/customer_edit_controller.py
@@ -36,7 +36,7 @@
         # rating the ticket is the one thing a closing email asks the customer to do
         if self.flags.get("ignore_closed_ticket_guard"):
             return
-        is_closed = old_doc.status == "Closed"
+        is_closed = old_doc.status is "Closed"
         is_rated = bool(old_doc.feedback)
         if is_closed or is_rated:
             text = _("Closed or rated tickets cannot be updated by non-agents")
```

### S4. customer_edit_controller.py:39 — core/ReplaceComparisonOperator_Eq_LtE (occurrence 0)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket/customer_edit_controller.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket/customer_edit_controller.py
@@ -36,7 +36,7 @@
         # rating the ticket is the one thing a closing email asks the customer to do
         if self.flags.get("ignore_closed_ticket_guard"):
             return
-        is_closed = old_doc.status == "Closed"
+        is_closed = old_doc.status <= "Closed"
         is_rated = bool(old_doc.feedback)
         if is_closed or is_rated:
             text = _("Closed or rated tickets cannot be updated by non-agents")
```

### S5. customer_edit_controller.py:84 — core/ReplaceBinaryOperator_BitOr_BitXor (occurrence 0)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket/customer_edit_controller.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket/customer_edit_controller.py
@@ -81,7 +81,7 @@
 
     def customer_writable_after_create(self) -> set[str]:
         """Close, rate, and what the template opens; replies reopen server-side."""
-        writable = set(CUSTOMER_ALWAYS_WRITABLE_FIELDS) | {
+        writable = set(CUSTOMER_ALWAYS_WRITABLE_FIELDS) ^ {
             row.fieldname
             for row in self.customer_writable_rows()
             if row.editable_after_creation
```

### S6. customer_edit_controller.py:90 — core/ReplaceComparisonOperator_Eq_Is (occurrence 1)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket/customer_edit_controller.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket/customer_edit_controller.py
@@ -87,7 +87,7 @@
             if row.editable_after_creation
         }
         # the portal only closes; Resolved is the agent's call and stops the SLA
-        if self.status == "Closed" or self.flags.get("customer_reply_reopen"):
+        if self.status is "Closed" or self.flags.get("customer_reply_reopen"):
             writable.add("status")
         return writable
```

### S7. customer_edit_controller.py:90 — core/ReplaceComparisonOperator_Eq_LtE (occurrence 1)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket/customer_edit_controller.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket/customer_edit_controller.py
@@ -87,7 +87,7 @@
             if row.editable_after_creation
         }
         # the portal only closes; Resolved is the agent's call and stops the SLA
-        if self.status == "Closed" or self.flags.get("customer_reply_reopen"):
+        if self.status <= "Closed" or self.flags.get("customer_reply_reopen"):
             writable.add("status")
         return writable
```

### S8. customer_edit_controller.py:101 — core/ReplaceComparisonOperator_NotEq_Gt (occurrence 1)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket/customer_edit_controller.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket/customer_edit_controller.py
@@ -98,7 +98,7 @@
         return [
             row
             for row in TicketFields().template_rows
-            if row.visible_to != "Agents"
+            if row.visible_to > "Agents"
             and row.fieldname in readable
             and row.fieldname not in SERVER_COMPUTED_FIELDS
         ]
```

### S9. customer_edit_controller.py:101 — core/ReplaceComparisonOperator_NotEq_IsNot (occurrence 1)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket/customer_edit_controller.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket/customer_edit_controller.py
@@ -98,7 +98,7 @@
         return [
             row
             for row in TicketFields().template_rows
-            if row.visible_to != "Agents"
+            if row.visible_to is not "Agents"
             and row.fieldname in readable
             and row.fieldname not in SERVER_COMPUTED_FIELDS
         ]
```

### S10. hd_ticket.py:414 — core/ReplaceComparisonOperator_NotEq_IsNot (occurrence 2)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
@@ -411,7 +411,7 @@
         )
         if (
             self.feedback_rating
-            or self.status_category != "Resolved"
+            or self.status_category is not "Resolved"
             or is_agent()
             or not self.has_agent_replied
             or not is_feedback_mandatory
```

### S11. hd_ticket.py:414 — core/ReplaceComparisonOperator_NotEq_Lt (occurrence 2)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
@@ -411,7 +411,7 @@
         )
         if (
             self.feedback_rating
-            or self.status_category != "Resolved"
+            or self.status_category < "Resolved"
             or is_agent()
             or not self.has_agent_replied
             or not is_feedback_mandatory
```

### S12. hd_ticket.py:951 — core/ReplaceComparisonOperator_NotEq_Gt (occurrence 3)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
@@ -948,7 +948,7 @@
         """Closing an already-resolved ticket wraps up an outcome, it is not a new one."""
         if self.is_new() or not self.has_value_changed("status"):
             return False
-        if self.status != "Closed":
+        if self.status > "Closed":
             return True
         previous = self.get_doc_before_save()
         return not previous or previous.status_category != "Resolved"
```

### S13. hd_ticket.py:951 — core/ReplaceComparisonOperator_NotEq_IsNot (occurrence 3)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
@@ -948,7 +948,7 @@
         """Closing an already-resolved ticket wraps up an outcome, it is not a new one."""
         if self.is_new() or not self.has_value_changed("status"):
             return False
-        if self.status != "Closed":
+        if self.status is not "Closed":
             return True
         previous = self.get_doc_before_save()
         return not previous or previous.status_category != "Resolved"
```

### S14. hd_ticket.py:954 — core/ReplaceComparisonOperator_NotEq_IsNot (occurrence 4)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
@@ -951,7 +951,7 @@
         if self.status != "Closed":
             return True
         previous = self.get_doc_before_save()
-        return not previous or previous.status_category != "Resolved"
+        return not previous or previous.status_category is not "Resolved"
 
     def set_resolution_date(self):
         """Stamp when the ticket was resolved. Runs for every ticket, with or
```

### S15. hd_ticket.py:954 — core/ReplaceComparisonOperator_NotEq_Lt (occurrence 4)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
@@ -951,7 +951,7 @@
         if self.status != "Closed":
             return True
         previous = self.get_doc_before_save()
-        return not previous or previous.status_category != "Resolved"
+        return not previous or previous.status_category < "Resolved"
 
     def set_resolution_date(self):
         """Stamp when the ticket was resolved. Runs for every ticket, with or
```

### S16. hd_ticket.py:962 — core/ReplaceComparisonOperator_NotEq_IsNot (occurrence 5)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
@@ -959,7 +959,7 @@
         if not self.is_valid_status_transition():
             return
 
-        if self.status_category != "Resolved":
+        if self.status_category is not "Resolved":
             self.resolution_date = None
             self.resolution_time = None  # apply_sla() won't run to clear it if no SLA is attached, so clear it here
             return
```

### S17. hd_ticket.py:962 — core/ReplaceComparisonOperator_NotEq_Lt (occurrence 5)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
@@ -959,7 +959,7 @@
         if not self.is_valid_status_transition():
             return
 
-        if self.status_category != "Resolved":
+        if self.status_category < "Resolved":
             self.resolution_date = None
             self.resolution_time = None  # apply_sla() won't run to clear it if no SLA is attached, so clear it here
             return
```

### S18. hd_ticket.py:1493 — core/ReplaceComparisonOperator_Eq_LtE (occurrence 18)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
@@ -1490,7 +1490,7 @@
 
 
 def close_tickets_after_n_days():
-    if frappe.db.get_single_value("HD Settings", "auto_close_tickets") == 0:
+    if frappe.db.get_single_value("HD Settings", "auto_close_tickets") <= 0:
         return
 
     status, days_threshold = frappe.db.get_value(
```

### S19. hd_ticket.py:1544 — core/ReplaceContinueWithBreak (occurrence 1)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
@@ -1541,7 +1541,7 @@
                 message=f"Failed to auto close ticket {doc.name} after {days_threshold} days. Error: {e}",
                 title="Auto Close Ticket Failed",
             )
-            continue
+            break
 
         frappe.db.commit()  # nosemgrep
```

### S20. hd_ticket_status.py:10 — core/ReplaceFalseWithTrue (occurrence 0)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
@@ -7,7 +7,7 @@
 
 
 class HDTicketStatus(Document):
-    def before_rename(self, old, new, merge=False):
+    def before_rename(self, old, new, merge=True):
         if old == "Closed":
             frappe.throw(_("The 'Closed' status cannot be renamed."))
```

### S21. hd_ticket_status.py:11 — core/ReplaceComparisonOperator_Eq_Is (occurrence 0)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
@@ -8,7 +8,7 @@
 
 class HDTicketStatus(Document):
     def before_rename(self, old, new, merge=False):
-        if old == "Closed":
+        if old is "Closed":
             frappe.throw(_("The 'Closed' status cannot be renamed."))
 
     def validate(self):
```

### S22. hd_ticket_status.py:11 — core/ReplaceComparisonOperator_Eq_LtE (occurrence 0)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
@@ -8,7 +8,7 @@
 
 class HDTicketStatus(Document):
     def before_rename(self, old, new, merge=False):
-        if old == "Closed":
+        if old <= "Closed":
             frappe.throw(_("The 'Closed' status cannot be renamed."))
 
     def validate(self):
```

### S23. hd_ticket_status.py:25 — core/ReplaceComparisonOperator_Eq_Is (occurrence 1)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
@@ -22,7 +22,7 @@
         old_name = (
             self.get_doc_before_save().name if self.get_doc_before_save() else None
         )
-        if old_name == "Closed" and not (
+        if old_name is "Closed" and not (
             self.has_value_changed("order") or self.has_value_changed("color")
         ):
             frappe.throw(
```

### S24. hd_ticket_status.py:47 — core/ReplaceComparisonOperator_NotEq_Gt (occurrence 0)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
@@ -44,7 +44,7 @@
             return
 
         # If category is being changed, check if we're removing the last status of a required category
-        if old_category != self.category:
+        if old_category > self.category:
             count = frappe.db.count(
                 "HD Ticket Status",
                 {"category": old_category, "name": ["!=", self.name]},
```

### S25. hd_ticket_status.py:47 — core/ReplaceComparisonOperator_NotEq_IsNot (occurrence 0)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
@@ -44,7 +44,7 @@
             return
 
         # If category is being changed, check if we're removing the last status of a required category
-        if old_category != self.category:
+        if old_category is not self.category:
             count = frappe.db.count(
                 "HD Ticket Status",
                 {"category": old_category, "name": ["!=", self.name]},
```

### S26. hd_ticket_status.py:53 — core/ReplaceComparisonOperator_Eq_LtE (occurrence 2)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
@@ -50,7 +50,7 @@
                 {"category": old_category, "name": ["!=", self.name]},
             )
 
-            if count == 0:
+            if count <= 0:
                 frappe.throw(
                     _(
                         f"At least one ticket status with category '{old_category}' must exist in the system."
```

### S27. hd_ticket_status.py:71 — core/ReplaceComparisonOperator_Eq_LtE (occurrence 3)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
@@ -68,7 +68,7 @@
                 "category": self.category,
             },
         )
-        if count == 0:
+        if count <= 0:
             frappe.throw(
                 _(
                     "At least one enabled status for <u>{0}</u> category must be enabled."
```

### S28. hd_ticket_status.py:113 — core/ReplaceComparisonOperator_Eq_Is (occurrence 2)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
@@ -110,7 +110,7 @@
             message = _(
                 "Cannot disable this status as it is linked in HD Settings:<br><br>"
             )
-            if self.name == settings_default_status:
+            if self.name is settings_default_status:
                 message += _("- Default Ticket Status<br>")
             if self.name == settings_reopen_status:
                 message += _("- Ticket Reopen Status<br>")
```

### S29. hd_ticket_status.py:113 — core/ReplaceComparisonOperator_Eq_LtE (occurrence 4)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
@@ -110,7 +110,7 @@
             message = _(
                 "Cannot disable this status as it is linked in HD Settings:<br><br>"
             )
-            if self.name == settings_default_status:
+            if self.name <= settings_default_status:
                 message += _("- Default Ticket Status<br>")
             if self.name == settings_reopen_status:
                 message += _("- Ticket Reopen Status<br>")
```

### S30. hd_ticket_status.py:115 — core/ReplaceComparisonOperator_Eq_Is (occurrence 3)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
@@ -112,7 +112,7 @@
             )
             if self.name == settings_default_status:
                 message += _("- Default Ticket Status<br>")
-            if self.name == settings_reopen_status:
+            if self.name is settings_reopen_status:
                 message += _("- Ticket Reopen Status<br>")
             message += _(
                 "<br>Please update HD Settings to use a different status before disabling this status."
```

### S31. hd_ticket_status.py:115 — core/ReplaceComparisonOperator_Eq_LtE (occurrence 5)

```diff
--- mutation diff ---
--- a/helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
+++ b/helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
@@ -112,7 +112,7 @@
             )
             if self.name == settings_default_status:
                 message += _("- Default Ticket Status<br>")
-            if self.name == settings_reopen_status:
+            if self.name <= settings_reopen_status:
                 message += _("- Ticket Reopen Status<br>")
             message += _(
                 "<br>Please update HD Settings to use a different status before disabling this status."
```
