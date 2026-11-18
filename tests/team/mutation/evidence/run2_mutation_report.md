# Mutation report

- Mutants in scope: 237
- Killed: 230
- Survived: 7
- Incompetent (not runnable): 0
- Abnormal / timeout: 0
- Skipped (outside scope): 746
- Still pending: 0
- **Mutation score: 97.0%** (killed / (killed + survived))

## By file

| File | Killed | Survived | Score |
|---|---|---|---|
| customer_edit_controller.py | 75 | 0 | 100.0% |
| hd_ticket.py | 78 | 4 | 95.1% |
| hd_ticket_status.py | 77 | 3 | 96.2% |

## By operator

| Operator | Killed | Survived |
|---|---|---|
| core/AddNot | 36 | 0 |
| core/ExceptionReplacer | 1 | 0 |
| core/NumberReplacer | 12 | 0 |
| core/ReplaceAndWithOr | 8 | 0 |
| core/ReplaceBinaryOperator_BitOr_Add | 1 | 0 |
| core/ReplaceBinaryOperator_BitOr_BitAnd | 1 | 0 |
| core/ReplaceBinaryOperator_BitOr_BitXor | 1 | 0 |
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
| core/ReplaceComparisonOperator_Eq_Is | 6 | 0 |
| core/ReplaceComparisonOperator_Eq_IsNot | 6 | 0 |
| core/ReplaceComparisonOperator_Eq_Lt | 9 | 0 |
| core/ReplaceComparisonOperator_Eq_LtE | 6 | 3 |
| core/ReplaceComparisonOperator_Eq_NotEq | 9 | 0 |
| core/ReplaceComparisonOperator_Gt_Eq | 1 | 0 |
| core/ReplaceComparisonOperator_Gt_GtE | 1 | 0 |
| core/ReplaceComparisonOperator_Gt_Lt | 1 | 0 |
| core/ReplaceComparisonOperator_Gt_LtE | 1 | 0 |
| core/ReplaceComparisonOperator_Gt_NotEq | 1 | 0 |
| core/ReplaceComparisonOperator_NotEq_Eq | 7 | 0 |
| core/ReplaceComparisonOperator_NotEq_Gt | 7 | 0 |
| core/ReplaceComparisonOperator_NotEq_GtE | 7 | 0 |
| core/ReplaceComparisonOperator_NotEq_Is | 7 | 0 |
| core/ReplaceComparisonOperator_NotEq_IsNot | 7 | 0 |
| core/ReplaceComparisonOperator_NotEq_Lt | 4 | 3 |
| core/ReplaceComparisonOperator_NotEq_LtE | 7 | 0 |
| core/ReplaceContinueWithBreak | 1 | 0 |
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

## Surviving mutants (7)

### S1. hd_ticket.py:414 — core/ReplaceComparisonOperator_NotEq_Lt (occurrence 2)

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

### S2. hd_ticket.py:954 — core/ReplaceComparisonOperator_NotEq_Lt (occurrence 4)

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

### S3. hd_ticket.py:962 — core/ReplaceComparisonOperator_NotEq_Lt (occurrence 5)

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

### S4. hd_ticket.py:1493 — core/ReplaceComparisonOperator_Eq_LtE (occurrence 18)

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

### S5. hd_ticket_status.py:10 — core/ReplaceFalseWithTrue (occurrence 0)

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

### S6. hd_ticket_status.py:53 — core/ReplaceComparisonOperator_Eq_LtE (occurrence 2)

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

### S7. hd_ticket_status.py:71 — core/ReplaceComparisonOperator_Eq_LtE (occurrence 3)

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
