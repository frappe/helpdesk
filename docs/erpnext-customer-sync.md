# Spec: ERPNext Customer Master Sync

## Overview

Bi-directional sync of customer records between Frappe Helpdesk (`HD Customer`) and ERPNext
(`Customer`). Both sides are equal — no creation blocks on either side. A customer can be born
in either system and the other side will receive it automatically. Field mapping uses
`frappe.model.mapper.get_mapped_doc` for extensibility. Inserts and updates to `customer_name`
and `image` are synced in both directions.

---

## Assumptions & Constraints

- ERPNext and Helpdesk are installed on the **same Frappe site**
- All sync logic is guarded by a single check: `"erpnext" in frappe.get_installed_apps()`.
  No settings toggle — if both apps are installed on the same site, the integration is active.
- Field mapping uses `frappe.model.mapper.get_mapped_doc`
- Sync is **bi-directional for inserts** — a customer born in either system syncs to the other immediately
- **Both directions propagate updates**: `customer_name` and `image` changes in either system are pushed to the linked record
- ERPNext → HD updates: `customer_name` and `image` are propagated on `on_update` (see Feature 7)
- HD → ERPNext updates: `customer_name` and `image` are propagated on `on_update` (see Feature 8)
- `HD Customer.name` maps to ERPNext `Customer.customer_name`
- ERPNext required field defaults: `customer_type = "Company"`. No `customer_group` is set —
  ERPNext applies its own default on insert.
- **Both sides are equal** — no source of truth, no creation blocks on either side
- Same-site only — multi-site and cross-site sync are out of scope
- No scheduled/nightly sync job — sync is on-demand (button) or real-time (insert/update hooks)

---

## Linked Fields

Each synced pair holds a cross-reference to the other. All "already synced?" checks use these
fields — **never name matching**.

| Field | On DocType | Type | Purpose |
|---|---|---|---|
| `erpnext_customer` | `HD Customer` | Data, read-only | Stores ERPNext `Customer.name` |
| `hd_customer` | ERPNext `Customer` | Data, read-only (custom field) | Stores `HD Customer.name` |

- `erpnext_customer` is added directly to `HD Customer` doctype JSON (Helpdesk owns this doctype)
- `hd_customer` is created as a Custom Field on ERPNext's `Customer` doctype programmatically
  (Helpdesk does not own ERPNext's doctype)

---

## Custom Field Setup

The `hd_customer` custom field on ERPNext `Customer` must be created before any sync runs.

### Patch

**File:** `helpdesk/patches/create_erpnext_customer_sync_fields.py`
**Registered in:** `helpdesk/helpdesk/patches.txt`

The patch:
1. Checks if `erpnext` is in installed apps. If not, exits silently.
2. Calls `setup_erpnext_customer_sync()` which:
   - Creates the `hd_customer` custom field on ERPNext `Customer` (idempotent)
   - Enqueues `sync_all_customers_with_erpnext()` as a background job for initial reconciliation

### `after_install` hook

**File:** `helpdesk/setup/install.py`

Same as the patch — handles the case where Helpdesk is installed after ERPNext.

---

## Installation Ordering

| Scenario | Handler |
|---|---|
| Both apps installed fresh together | Patch runs on `bench migrate`, fields created, initial reconciliation done |
| Helpdesk installed after ERPNext | `after_install` hook — fields created, reconciliation done |
| ERPNext installed after Helpdesk | Patch already ran and was skipped. ERPNext's own `after_install` calls `create_helpdesk_fields_in_customer()` to create the custom field. For initial reconciliation of existing records, use the "Sync with ERPNext" button in the HD Customer list. |
| Ongoing — customer created in either app | `after_insert` hooks handle real-time sync |

---

## Feature 1: HD Customer → ERPNext on Insert

**Trigger:** `HDCustomer.after_insert`

**Logic:**
1. Check `self.flags.ignore_erpnext_sync` — if set, return (loop guard)
2. Check `"erpnext" in frappe.get_installed_apps()` — if false, return
3. Check `self.erpnext_customer` is blank — if already set, return
4. Use `get_mapped_doc` to map `HD Customer` → ERPNext `Customer`
   - `field_map`: `customer_name → customer_name`, `image → image`
5. Set `customer_type = "Company"` on the new ERPNext doc
6. Set `flags.ignore_erpnext_sync = True` on the new ERPNext doc (loop guard)
7. Insert ERPNext `Customer` with `ignore_permissions=True`
8. `self.db_set("erpnext_customer", erp_doc.name)` — no save trigger
9. `frappe.db.set_value("Customer", erp_doc.name, "hd_customer", self.name)` — set reverse link

**Files:**
- `helpdesk/helpdesk/doctype/hd_customer/hd_customer.py`

---

## Feature 2: ERPNext Customer → HD Customer on Insert

**Trigger:** `doc_events["Customer"]["after_insert"]` in `hooks.py`

**Logic (`create_or_link_hd_customer(doc)` in `erpnext/customer.py`):**

Resolution order — to handle ERPNext's non-unique `customer_name`:

1. Check `doc.flags.ignore_erpnext_sync` — if set, return (loop guard)
2. Check `"erpnext" in frappe.get_installed_apps()` — if false, return
3. Check `doc.hd_customer` is blank — if already set, return
4. **Step 1 — match by `customer_name`:** if HD Customer named `doc.customer_name` exists → set cross-links on both sides, done
5. **Step 2 — match by ERPNext `name`:** if HD Customer named `doc.name` exists → set cross-links, done
6. **Step 3 — create:** neither exists → create HD Customer using `doc.name` (the unique ERPNext ID) as `customer_name`, set cross-links

Using `doc.name` in step 3 guarantees uniqueness even when multiple ERPNext Customers share the same `customer_name`.

Cross-link helper `set_links(erp_name, hd_name)` sets `erpnext_customer` on HD side and `hd_customer` on ERPNext side.

**Files:**
- `helpdesk/hooks.py` — `doc_events = {"Customer": {"after_insert": ..., "on_update": ...}}`
- `helpdesk/helpdesk/integrations/erpnext/customer.py` — `after_insert`, `create_or_link_hd_customer`, `set_links`

---

## Feature 3: ERPNext Customer Form — "Sync to Helpdesk" Button

**Trigger:** Button injected into the ERPNext Customer form via `doctype_js`

**How it works:**
- `helpdesk/hooks.py` registers `doctype_js = {"Customer": "public/erpnext/customer.js"}`
- Button shown only when `!frm.doc.__islocal` and `hd_customer` is blank
- On click: calls `helpdesk.helpdesk.integrations.erpnext.customer.sync_erpnext_customer_to_hd`
- On success: reloads the form so the `hd_customer` field shows the new value

**Files:**
- `helpdesk/hooks.py`
- `helpdesk/public/erpnext/customer.js`
- `helpdesk/helpdesk/integrations/erpnext/customer.py` — `sync_erpnext_customer_to_hd(customer_name)`

---

## Feature 4: ERPNext Customer List — Bulk "Sync to Helpdesk" Action

**Trigger:** Action injected into the ERPNext Customer list via `doctype_list_js`

**How it works:**
- `helpdesk/hooks.py` registers `doctype_list_js = {"Customer": "public/erpnext/customer_list.js"}`
- On click: takes selected rows, calls `helpdesk.helpdesk.integrations.erpnext.customer.bulk_sync_erpnext_customers_to_hd`
- Shows a summary toast: "X created, Y skipped (already synced)"

**Files:**
- `helpdesk/hooks.py`
- `helpdesk/public/erpnext/customer_list.js`
- `helpdesk/helpdesk/integrations/erpnext/customer.py` — `bulk_sync_erpnext_customers_to_hd(customer_names)`

---

## Feature 5: HD Customer List — "Sync with ERPNext" Button

**Trigger:** Button in the HD Customer list header (top-right), shown only when there are
unsynced customers on either side (i.e. `get_unsynced_count()` returns a total > 0).
Also shown while a sync is in progress.

**How it works:**
- Button is visible only when `configStore.isErpnextInstalled && (hasUnsynced || isSyncing)`
- On click: calls `helpdesk.helpdesk.integrations.erpnext.customer.sync_all_customers_with_erpnext`
- Backend emits `helpdesk:erpnext-sync-start` via `frappe.publish_realtime` before sync starts
  and `helpdesk:erpnext-sync-end` in a `finally` block when done
- Frontend listens to these socket events to show/hide the loading spinner on the button
- On success: toast shown, list and unsynced count reloaded

**Backend logic (`sync_all_customers_with_erpnext`):**

HD → ERPNext direction first:
1. Fetch all `HD Customer` records where `erpnext_customer` is blank
2. For each, call `hd_doc.sync_to_erpnext()`

ERPNext → HD direction second:
1. Fetch all ERPNext `Customer` records where `hd_customer` is blank
2. For each, call `create_or_link_hd_customer(erp_doc)` from `integrations/erpnext/customer.py`

**`get_unsynced_count()` API (now `is_unsynced()`):**
Returns `True` when the total count of HD Customers and ERPNext Customers differ (meaning sync
is needed), `False` otherwise. Called on page mount and after every sync completes.

**Files:**
- `helpdesk/helpdesk/integrations/erpnext/customer.py` — `sync_all_customers_with_erpnext()`, `is_unsynced()`
- `desk/src/pages/desk/customer/Customers.vue`
- `desk/src/stores/config.ts` — `isErpnextInstalled` computed

---

## Feature 6: "Create Customer" in HD — Always via NewCustomerDialog

The "Create" button in the HD Customer list always opens `NewCustomerDialog` regardless of
whether ERPNext is installed. When the HD Customer is saved, `after_insert` automatically
syncs it to ERPNext (Feature 1). There is no intermediate dialog redirecting to ERPNext.

`ERPNextCreateCustomerDialog.vue` has been removed.

**Files:**
- `desk/src/pages/desk/customer/Customers.vue` — `handleCreate()` always opens `NewCustomerDialog`

---

---

## Feature 7: ERPNext Customer → HD Customer on Update

**Trigger:** `doc_events["Customer"]["on_update"]` in `hooks.py`

**Logic (`on_update(doc, method)` in `integrations/erpnext/customer.py`):**

1. Check `doc.flags.ignore_erpnext_sync` — if set, return (loop guard)
2. Check `"erpnext" in frappe.get_installed_apps()` — if false, return
3. Check `doc.hd_customer` — if blank (not linked), return
4. Check `doc.has_value_changed("customer_name") or doc.has_value_changed("image")` — if neither changed, return (no unnecessary writes)
5. `frappe.db.set_value("HD Customer", hd_customer_name, {"customer_name": ..., "image": ...}, update_modified=False)`

**Why `db.set_value` and not `doc.save()`:**
- Direct DB write — does not fire the HD Customer `on_update` hook, so no loop is possible
- `update_modified=False` — HD Customer's `modified` timestamp is not bumped by a sync-originated write

**Why `on_rename` is not implemented:**
- ERPNext `name` changes happen via `frappe.rename_doc`, which fires `on_rename`, not `on_update`
- `has_value_changed("name")` will never be true in `on_update`
- Name/rename sync is out of scope

**Files:**
- `helpdesk/hooks.py` — `doc_events = {"Customer": {"after_insert": ..., "on_update": ...}}`
- `helpdesk/helpdesk/integrations/erpnext/customer.py` — `on_update`

---

## Feature 8: HD Customer → ERPNext Customer on Update

**Trigger:** `HDCustomer.on_update` in `hd_customer.py`

**Logic (`sync_update_to_erpnext()`):**

1. Check `"erpnext" in frappe.get_installed_apps()` — if false, return
2. Check `self.flags.ignore_erpnext_sync` — if set, return (loop guard)
3. Check `self.erpnext_customer` — if blank (not linked), return
4. Check `self.has_value_changed("customer_name") or self.has_value_changed("image")` — if neither changed, return (no unnecessary writes)
5. `frappe.db.set_value("Customer", self.erpnext_customer, {"customer_name": ..., "image": ...}, update_modified=False)`

**Why `db.set_value` and not `doc.save()`:**
- Direct DB write — does not fire the ERPNext Customer `on_update` hook, so no loop is possible
- `update_modified=False` — ERPNext Customer's `modified` timestamp is not bumped by a sync-originated write

**Files:**
- `helpdesk/helpdesk/doctype/hd_customer/hd_customer.py` — `on_update` + `sync_update_to_erpnext()`

---

### B1 — Infinite sync loop

**Problem:** HD Customer `after_insert` → creates ERPNext Customer → ERPNext Customer
`after_insert` fires → tries to create HD Customer → loop.

**Solution:** `doc.flags.ignore_erpnext_sync = True` is set on every programmatically created
doc before insert. Both `after_insert` handlers check this flag at the very top and return
immediately if set. Flags are in-memory only and do not persist across saves.

---

### B2 — `customer_name` is not unique in ERPNext

**Problem:** ERPNext does not enforce uniqueness on `customer_name`. Matching by name is
unreliable.

**Solution:** All lookups use the linked field (`erpnext_customer` / `hd_customer`), never
name matching.

---

### B3 — ERPNext `customer_name` is not unique

**Problem:** Multiple ERPNext Customers can share the same `customer_name` (e.g. two records
both named `"ABC"`). HD Customer uses `customer_name` as its unique `name` — inserting a second
`"ABC"` would crash with a duplicate name error. Additionally, simply linking to an existing HD
Customer when `customer_name` matches is wrong if that HD Customer is already linked to a
different ERPNext Customer.

**Solution:** `create_or_link_hd_customer` uses a three-step resolution:
1. If HD Customer named `erp.customer_name` exists **and has no `erpnext_customer` set** → link it (unlinked record, safe to claim)
2. If HD Customer named `erp.name` exists **and has no `erpnext_customer` set** → link it
3. Otherwise → create HD Customer with `customer_name = erp.name` (the unique ERPNext ID, never collides)

The "only if unlinked" guard in steps 1 and 2 ensures that a second ERPNext Customer with the
same `customer_name` (e.g. `ABC - 1` when `ABC` is already linked) always falls through to step
3 and gets its own HD Customer record named after the ERPNext ID.

---

### B4 — ERPNext Customer deleted, HD link is stale

**Problem:** An ERPNext Customer is deleted. The corresponding HD Customer still has
`erpnext_customer` pointing to a non-existent doc.

**Solution:** `_sync_hd_to_erpnext` only queries HD Customers where `erpnext_customer` is
blank, so stale links are not re-processed. Out of scope for now — no auto-deletion or
stale-link clearing is implemented.

---

### B5 — ERPNext installed after Helpdesk (patch already ran and was skipped)

**Problem:** The patch ran when only Helpdesk was installed, saw ERPNext was absent, skipped,
and was marked done. When ERPNext is later added, the `hd_customer` custom field does not
exist on `Customer`, so any sync attempt errors with a missing column.

**Solution:** ERPNext's own `after_install` (`erpnext/setup/install.py`) calls
`create_helpdesk_fields_in_customer()` (imported from
`helpdesk.helpdesk.integrations.erpnext.customer`), which creates the custom field immediately
when ERPNext is installed. For initial reconciliation of existing records, use the
"Sync with ERPNext" button in the HD Customer list.

---

### B6 — Patch idempotency

**Solution:**
- Custom field creation checks existence first
- `sync_all_customers_with_erpnext` only processes records where the linked field is blank

---

## Complete File Manifest

| File | Status | Purpose |
|---|---|---|
| `helpdesk/helpdesk/doctype/hd_customer/hd_customer.json` | Modified | Added `erpnext_customer` Data field (read-only) |
| `helpdesk/helpdesk/doctype/hd_customer/hd_customer.py` | Modified | `after_insert` → `sync_to_erpnext()`; `on_update` → `sync_update_to_erpnext()` |
| `helpdesk/helpdesk/doctype/hd_customer/test_hd_customer.py` | Modified | Integration tests: HD↔ERP insert sync, on_update propagation (both directions), sync_all |
| `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` | Modified | Removed `erpnext_integration_enabled` field and section |
| `helpdesk/hooks.py` | Modified | `doc_events`, `doctype_js`, `doctype_list_js` |
| `helpdesk/helpdesk/integrations/erpnext/__init__.py` | New | Package marker for ERPNext integration module |
| `helpdesk/helpdesk/integrations/erpnext/customer.py` | New | All ERPNext Customer sync logic: `after_insert`, `on_update` hooks; `create_or_link_hd_customer`, `set_links`; whitelisted API functions (`is_unsynced`, `sync_erpnext_customer_to_hd`, `bulk_sync_erpnext_customers_to_hd`, `sync_all_customers_with_erpnext`); `setup_erpnext_customer_sync()` |
| `helpdesk/helpdesk/integrations/erpnext/test_customer_sync.py` | New | Integration tests: bulk_sync, sync_hd_to_erpnext, sync_erpnext_to_hd, is_unsynced |
| `helpdesk/api/config.py` | Modified | Exposes `apps` list; `erpnext_integration_enabled` removed |
| `helpdesk/public/erpnext/customer.js` | New | "Sync to Helpdesk" button on ERPNext Customer form |
| `helpdesk/public/erpnext/customer_list.js` | New | Bulk "Sync to Helpdesk" action on ERPNext Customer list |
| `helpdesk/setup/install.py` | Modified | Calls `setup_erpnext_customer_sync()` in `after_install` |
| `helpdesk/patches/create_erpnext_customer_sync_fields.py` | New | Patch: guard on both apps + call `setup_erpnext_customer_sync()` |
| `helpdesk/helpdesk/patches.txt` | Modified | Registered both patches |
| `helpdesk/test_utils.py` | Modified | `_setup_erpnext_custom_fields()` in `before_tests`; `make_erp_customer()`; `ERPNEXT_NOT_INSTALLED` constant |
| `desk/src/stores/config.ts` | Modified | `isErpnextInstalled` computed; `isErpnextIntegrationEnabled` removed |
| `desk/src/pages/desk/customer/Customers.vue` | Modified | Sync button, socket listeners, `handleCreate()` always opens `NewCustomerDialog` |
| ~~`desk/src/components/modals/ERPNextCreateCustomerDialog.vue`~~ | Deleted | Removed — customers are always created directly in HD; `after_insert` syncs to ERPNext |
| ~~`helpdesk/overrides/customer.py`~~ | Deleted | Merged into `helpdesk/helpdesk/integrations/erpnext/customer.py` |
| ~~`helpdesk/api/customer.py`~~ | Deleted | Merged into `helpdesk/helpdesk/integrations/erpnext/customer.py` |
| ~~`helpdesk/api/test_customer_sync.py`~~ | Deleted | Moved to `helpdesk/helpdesk/integrations/erpnext/test_customer_sync.py` |
| ~~`helpdesk/public/js/customer.js`~~ | Deleted | Moved to `helpdesk/public/erpnext/customer.js` |
| ~~`helpdesk/public/js/customer_list.js`~~ | Deleted | Moved to `helpdesk/public/erpnext/customer_list.js` |

---

## Out of Scope

- Syncing fields other than `customer_name` and `image`. Additional fields can be added
  to the `get_mapped_doc` field map (for inserts) and the `db.set_value` call (for updates) trivially.
- ERPNext Customer renamed (`name` key changed via `frappe.rename_doc`) — needs `on_rename` hook, out of scope
- Multi-site / cross-site sync
- Blocking customer creation on either side
- Nightly scheduled reconciliation for already-synced records — on-demand button only
