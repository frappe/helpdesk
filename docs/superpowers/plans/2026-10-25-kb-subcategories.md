# Knowledge Base Subcategories Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a knowledge base Category hold one level of Subcategories across the backend, the agent desk and the Studio customer portal, and fix four category bugs that exist today.

**Architecture:** A self Link `parent_article_category` on HD Article Category, guarded to one level. Access stays on HD Article: every category rule reads the **branch** (a Category plus its Subcategories) through one helper, `get_branch`. The portal and desk receive a flat category list carrying `parent_article_category` and a display `label`, and nest it on the client.

**Tech Stack:** Frappe (Python, `frappe.qb`, IntegrationTestCase), Vue 3 + frappe-ui (desk `desk/src`), Studio portal pages (`studio/helpdesk`, `.ts` scripts + `.json` block trees), `@helpdesk/shared`, Playwright.

**Spec:** `docs/superpowers/specs/2026-10-25-kb-subcategories-design.md` (decisions numbered 1–32; tasks cite them as D1…D32). Terms: `CONTEXT.md`. Shape: `docs/adr/0001-one-level-subcategories-with-derived-access.md`.

## Global Constraints

- Work in the worktree `apps/.hd-kb-subcategories` on branch `feat/kb-subcategories` (based on `frappe/helpdesk` `develop` @ `4f41f4c21`).
- Fieldname `parent_article_category`, label `Parent Category`. Never reuse `parent_category`. Never touch `parent`, `parenttype` or `parentfield`.
- The label separator is ` › ` (U+203A with a space on each side): `"Billing › FAQ"`.
- Run tests only on `e2e.localhost`, never on `studio.localhost`. Start the bench redis first.
  - Backend: `bench --site e2e.localhost run-tests --app helpdesk --module <module> [--test <name>] --skip-before-tests`
  - e2e: serve with `bench --site e2e.localhost serve --port 8020 --noreload`, plus `node apps/frappe/socketio.js` and `bench worker`. Run Playwright from `apps/helpdesk` (the only place `@playwright/test` resolves). The `e2e` folder comes from this worktree.
- Rebuild the portal after `studio/` changes: `bench build-studio-app helpdesk --site e2e.localhost`.
- To serve this branch on `e2e.localhost`, the bench's `apps/helpdesk` must be on it. Point that checkout at this branch only after confirming with the user, because `studio.localhost` serves the same checkout.
- Test helpers live in `helpdesk/test_utils.py` only. Backend API tests go in `helpdesk/tests/api/`. DocType tests sit next to their DocType.
- Translate every new user-facing string: `_()` in Python, `__()` in TypeScript and Vue.
- Commit messages are conventional (`feat(kb):`, `fix(kb):`, `test(kb):`) and end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **A Category with no Articles of its own but a readable Subcategory**: guests and customers see it on home, in the sidebar and through `has_permission`, and its page shows the Subcategory cards. Tested in Task 3 (`test_a_parent_with_only_a_readable_subcategory_is_shown`) and Task 9 (e2e).
2. **Two agents parenting A under B and B under A at the same moment**: one of the two saves must fail. The guard locks the parent row (`for_update=True`) in `validate`. A unit test can't race two transactions, so Task 2 tests the sequential case (`test_a_category_with_subcategories_cannot_get_a_parent`) and the reviewer checks the lock.
3. **A pinned Category moved under another one**: it disappears from home and the desk shows the unpin note. Task 2 tests `test_a_pinned_category_is_unpinned_when_it_gets_a_parent`, and Task 7 shows the toast.
4. **Deleting a branch whose Articles have feedback or citing tickets**: nothing fails halfway. Cited Articles end up Archived with no category, and feedback rows are deleted with their Article. Task 5 tests `test_branch_delete_archives_cited_articles` and `test_deleting_an_article_with_feedback_removes_the_feedback`.
5. **A Subcategory with the same name as another**: every picker, search hit, desk group and breadcrumb reads `Category › Subcategory`. Task 4 tests `test_labels_name_the_parent`, and Task 6 tests `test_group_labels_name_the_parent`.

---

### Task 1: Fix today's category bugs (D28–D30)

**Files:**
- Modify: `helpdesk/helpdesk/doctype/hd_article/hd_article.py` (`validate`, `before_save`)
- Modify: `helpdesk/helpdesk/doctype/hd_article_category/hd_article_category.py` (`get_category_visibility`, `move_category_articles`, new `on_update`, new `reindex_category_articles`)
- Test: `helpdesk/helpdesk/doctype/hd_article/test_hd_article.py`, `helpdesk/tests/api/test_knowledge_base.py` (class `TestCategoryAccess`)
- Commit with it: `CONTEXT.md`, `docs/adr/0001-…`, `docs/superpowers/specs/…`, this plan

**Interfaces:**
- Produces: `reindex_category_articles(category: str) -> None`, which enqueues `helpdesk.search.update_article_index` for each Article in `category` (`enqueue_after_commit=True`, queue `short`, matching `HDArticle.update_search_index`).
- Produces: `get_category_visibility(category: str) -> str | None`, with the same signature but the D29 rule. Task 3 widens it to the branch.

- [ ] **Step 1: Write the failing tests**

```python
# test_hd_article.py
def test_archiving_the_last_article_is_refused(self):
    category = make_article_category(unique_name("Solo")).name
    article = frappe.get_doc("HD Article", make_article(category=category))
    with self.assertRaises(frappe.ValidationError):
        article.update({"status": "Archived"}).save()
    self.assertEqual(frappe.db.get_value("HD Article", article.name, "category"), category)

# test_knowledge_base.py, TestCategoryAccess
def test_a_private_draft_does_not_make_access_mixed(self):
    # Published: Customers; one Draft: Private
    self.assertEqual(get_category_visibility(self.category), "Customers")

def test_a_category_of_drafts_reads_its_drafts(self):
    # only Draft articles, all Private
    self.assertEqual(get_category_visibility(category), "Private")

def test_merging_reindexes_the_moved_articles(self):
    with patch("frappe.enqueue") as enqueue:
        merge_category(source, target)
    indexed = {c.kwargs["article"] for c in enqueue.call_args_list
               if c.args[0] == "helpdesk.search.update_article_index"}
    self.assertEqual(indexed, set(source_articles))

def test_renaming_a_category_reindexes_its_articles(self):
    # same patch; save category_name change; assert its articles enqueued
```

- [ ] **Step 2: Run them and check they fail**

Run: `bench --site e2e.localhost run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_article.test_hd_article --skip-before-tests`, then the same with `--module helpdesk.tests.api.test_knowledge_base`.
Expected: the 5 new tests FAIL.

- [ ] **Step 3: Implement**

- `HDArticle.validate`: clear `category` for Archived **before** `validate_article_category` runs, and remove that line from `before_save`.
- `get_category_visibility`: read the distinct visibilities of Published Articles. If there are none, read every Article.
- `move_category_articles`: after the bulk `set_value`, call `reindex_category_articles(target)`.
- `HDArticleCategory.on_update`: if `has_value_changed("category_name")` and the doc is not new, call `reindex_category_articles(self.name)`.

- [ ] **Step 4: Run them and check they pass**

Same commands. Expected: PASS, including the existing `TestCategoryAccess` and `TestHDArticleCategory`.

- [ ] **Step 5: Commit**

```bash
git add CONTEXT.md docs helpdesk/helpdesk/doctype/hd_article helpdesk/helpdesk/doctype/hd_article_category helpdesk/tests/api/test_knowledge_base.py
git commit -m "fix(kb): keep categories non-empty on archive, read access from published articles, reindex moved articles"
```

---

### Task 2: Parent field and the one-level guard (D1, D2, D5, D6, D9)

**Files:**
- Modify: `helpdesk/helpdesk/doctype/hd_article_category/hd_article_category.json` (add the field after `category_name`)
- Modify: `helpdesk/helpdesk/doctype/hd_article_category/hd_article_category.py`
- Test: `helpdesk/helpdesk/doctype/hd_article_category/test_hd_article_category.py` (new class `TestSubcategory`)

**Interfaces:**
- Produces: field `parent_article_category` (Link → HD Article Category, label "Parent Category").
- Produces: `get_subcategories(category: str) -> list[str]` (names, `category_name asc`), `get_branch(category: str) -> list[str]` (`[category, *subcategories]`), `get_parent(category: str) -> str | None`.
- Produces: `HDArticleCategory.validate_parent()`, which runs inside `validate`.
- Produces: `doc.flags.unpinned = True` when the save unpinned the doc. Task 7 reads it.

- [ ] **Step 1: Write the failing tests**

```python
class TestSubcategory(IntegrationTestCase):
    def test_a_category_cannot_be_its_own_parent(self): ...        # ValidationError
    def test_a_subcategory_cannot_get_subcategories(self): ...      # parent=a_subcategory → ValidationError
    def test_a_category_with_subcategories_cannot_get_a_parent(self): ...  # ValidationError
    def test_general_cannot_become_a_subcategory(self): ...         # ValidationError
    def test_general_can_hold_subcategories(self): ...              # saves
    def test_a_pinned_category_is_unpinned_when_it_gets_a_parent(self):
        doc = make_article_category(unique_name("Pinned"), pinned=1, pinned_order=1)
        doc.update({"parent_article_category": parent}).save()
        self.assertEqual((doc.pinned, doc.pinned_order), (0, 0))
        self.assertTrue(doc.flags.unpinned)
    def test_a_subcategory_cannot_be_pinned(self): ...              # pinned=1 with a parent → ValidationError
    def test_the_branch_is_the_category_then_its_subcategories(self):
        self.assertEqual(get_branch(parent), [parent, sub_a, sub_b])  # alphabetical (D8)
```

- [ ] **Step 2: Run them and check they fail**

Run: `bench --site e2e.localhost run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_article_category.test_hd_article_category --skip-before-tests`
Expected: FAIL (the field is missing).

- [ ] **Step 3: Implement**

- Add the field and run `bench --site e2e.localhost migrate`.
- `validate_parent`: refuse the category as its own parent, a parent that has a parent, giving a parent to a category that has Subcategories, and General as a child (D5). Read the parent's own `parent_article_category` with `frappe.db.get_value(..., for_update=True)`. That row lock is the race guard (Review Focus 2).
- Unpinning (D9): when the category gets a parent while pinned, it becomes unpinned (`pinned`/`pinned_order` set to 0) and `flags.unpinned` is set. A Subcategory saved with `pinned=1` and no change of parent is refused.
- Add the three helpers next to `get_category_visibility`.

- [ ] **Step 4: Run them and check they pass**

Same command. Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -m "feat(kb): subcategories one level under a category"`

---

### Task 3: Branch access (D4, D10–D13)

**Files:**
- Modify: `helpdesk/helpdesk/doctype/hd_article_category/hd_article_category.py` (`permission_query`, `has_permission`, `get_category_visibility`, `check_category_length`, `on_update`)
- Modify: `helpdesk/helpdesk/doctype/hd_article/hd_article.py` (`inherit_category_visibility`)
- Modify: `helpdesk/api/knowledge_base.py` (`set_category_visibility`)
- Test: `helpdesk/tests/api/test_knowledge_base.py` (new class `TestSubcategoryAccess`)

**Interfaces:**
- Consumes: `get_branch`, `get_parent`, `get_subcategories` (Task 2).
- Produces: `get_category_visibility(category)`, which now reads the whole branch.
- Produces: `narrow_category_articles(category: str, visibility: str | None) -> None`, which saves each Article in `category` whose visibility `get_stricter_visibility` narrows. Task 5 and Task 6 reuse it.

- [ ] **Step 1: Write the failing tests**

```python
class TestSubcategoryAccess(IntegrationTestCase):
    def test_a_parent_with_only_a_readable_subcategory_is_shown(self):
        # parent: no articles; sub: one Public article
        with self.set_user("Guest"):
            # permission_query and has_permission only; get_categories follows in Task 4
            self.assertIn(parent, frappe.get_list("HD Article Category", pluck="name"))
            self.assertTrue(frappe.has_permission("HD Article Category", "read", parent))
    def test_a_private_subcategory_keeps_its_parent_hidden(self): ...  # all Private → parent absent for a customer
    def test_access_reads_the_whole_branch(self): ...      # parent Customers + sub Public → None (Mixed)
    def test_setting_access_rewrites_subcategory_articles(self):
        set_category_visibility(parent, "Private")
        self.assertEqual(set(frappe.get_all("HD Article", {"category": ["in", [parent, sub]]}, pluck="visibility", distinct=True)), {"Private"})
    def test_getting_a_parent_narrows_its_articles(self):
        # parent branch Customers; Public category gets parent → its articles become Customers
    def test_getting_a_parent_never_widens(self): ...      # Private stays Private under a Public parent
    def test_a_parent_may_lose_its_last_own_article(self): ...  # has sub; moving its last article out saves
    def test_a_first_article_in_a_new_subcategory_inherits_the_parent(self):
        # parent branch Private; new sub; make_article(category=sub, visibility="Customers") → Private
```

- [ ] **Step 2: Run them and check they fail**

Run: `bench --site e2e.localhost run-tests --app helpdesk --module helpdesk.tests.api.test_knowledge_base --test <each> --skip-before-tests`
Expected: FAIL.

- [ ] **Step 3: Implement**

- `permission_query`: a category is readable when an Article in its own category is readable, or when it is the `parent_article_category` of such a category. Write it as one SQL condition built from `article_permission_query(user)`. It is one level deep, so it needs no recursion.
- `has_permission`: filter Articles with `category=["in", get_branch(doc.name)]`.
- `get_category_visibility`: apply the D29 rule from Task 1 over `category in get_branch(category)`.
- `set_category_visibility`: filter on `category in get_branch(category)`.
- `check_category_length`: return early when the category has Subcategories.
- `inherit_category_visibility`: fall back to the parent's visibility when the Article's own category reads `None`.
- `HDArticleCategory.on_update`: when `parent_article_category` changed to a value, call `narrow_category_articles(self.name, get_category_visibility(parent))`. Read that before the move counts this category in, through `get_doc_before_save` or by reading the parent's branch without `self.name`.

- [ ] **Step 4: Run them and check they pass**

Run the whole module. Expected: PASS, including the existing `TestCustomersOnlyArticles`, `TestArticlePermissions` and `TestCategoryAccess`.

- [ ] **Step 5: Commit**

`git commit -m "feat(kb): read category access and visibility across subcategories"`

---

### Task 4: Read APIs carry the hierarchy (D7, D11, D24)

**Files:**
- Modify: `helpdesk/api/knowledge_base.py` (`PUBLIC_CATEGORY_FIELDS`, `_get_categories`, `get_kb_sidebar`, `get_article`, `search_articles`/`_get_search_hit`, new `get_category_options`)
- Modify: `helpdesk/helpdesk/doctype/hd_article_category/hd_article_category.py` (new `get_category_labels`)
- Test: `helpdesk/tests/api/test_knowledge_base.py` (class `TestSubcategoryReads`)

**Interfaces:**
- Produces: `get_category_labels(names: list[str]) -> dict[str, str]`, which maps a top-level name to `category_name` and a Subcategory to `"<parent name> › <name>"`. It runs one query.
- Produces: rows from `_get_categories` (and so from `get_categories` and `get_kb_sidebar`) gain `parent_article_category` and `label`. `article_count` on a parent is its own Articles plus its Subcategories' Articles, readable ones only. A parent with no readable Articles of its own still appears when a Subcategory is readable.
- Produces: `get_article(name)` gains `category_label`, `parent_article_category` and `parent_category_name`. Search hits gain `category_label`, and `category_name` stays as it is for compatibility.
- Produces: `@frappe.whitelist() get_category_options(exclude: str | None = None) -> list[dict]`, which returns `{value, label, parent_article_category, has_subcategories}` for every category, sorted by label parts with General first. It requires `HD Article` write permission.

- [ ] **Step 1: Write the failing tests**

```python
class TestSubcategoryReads(IntegrationTestCase):
    def test_labels_name_the_parent(self):
        self.assertEqual(get_category_labels([parent, sub]), {parent: "Billing", sub: "Billing › FAQ"})
    def test_a_parent_counts_its_subcategories(self):
        self.assertEqual(category_row(parent).article_count, 3)   # 1 own + 2 in sub
    def test_a_parent_counts_only_what_the_reader_reads(self): ...  # guest: Private sub article excluded
    def test_rows_carry_their_parent(self):
        self.assertEqual(category_row(sub).parent_article_category, parent)
    def test_an_article_carries_its_category_label(self): ...  # get_article(...).category_label == "Billing › FAQ"
    def test_a_search_hit_carries_its_category_label(self): ...  # use_test_index, as test_search.py does
    def test_category_options_put_subcategories_after_their_parent(self):
        labels = [row["label"] for row in get_category_options()]
        self.assertLess(labels.index("Billing"), labels.index("Billing › FAQ"))
        self.assertLess(labels.index("Billing › FAQ"), labels.index("Billing Extra"))
        self.assertEqual(labels[0], "General")
    def test_a_customer_cannot_list_category_options(self): ...  # PermissionError
```

- [ ] **Step 2: Run them and check they fail.** Expected: FAIL.

- [ ] **Step 3: Implement.** Sort key: `(label != "General", [part.casefold() for part in label.split(" › ")])`. In `_get_categories`, add each Subcategory's counts and creators to its parent, then fetch the categories for `counts ∪ parents of counted`.

- [ ] **Step 4: Run them and check they pass.** Run the whole module. Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -m "feat(kb): category reads carry parent, label and branch counts"`

---

### Task 5: Delete a Category or a whole branch (D14–D17, D31)

**Files:**
- Modify: `helpdesk/helpdesk/doctype/hd_article_category/hd_article_category.py` (`on_trash`, `move_articles_to_general`, `check_category_length`)
- Modify: `helpdesk/api/knowledge_base.py` (`delete_articles`, new `get_category_delete_summary`, new `delete_category`)
- Test: `helpdesk/tests/api/test_knowledge_base.py` (class `TestCategoryDelete`)
- Modify: `helpdesk/test_utils.py`, only if `make_ticket` cannot take `source_article`. Add `make_cited_article(category)` there with a docstring.

**Interfaces:**
- Consumes: `get_subcategories`, `get_parent` (Task 2) and `narrow_category_articles` (Task 3).
- Produces: `delete_or_archive_article(name: str) -> bool` (True when it archived). It deletes the Article's `HD Article Feedback` rows. When any `HD Ticket` has `source_article == name` it archives the Article instead (status Archived, category cleared, reindexed). Otherwise it calls `frappe.delete_doc`.
- Produces: `@frappe.whitelist() get_category_delete_summary(category: str) -> {"articles": int, "subcategories": int, "cited": int}`, covering the whole branch.
- Produces: `@frappe.whitelist(methods=["POST"]) delete_category(category: str, delete_articles: bool = False) -> {"archived": int}`. It requires `HD Article Category` delete permission and refuses General.
- `frappe.flags.deleting_category` holds the branch being deleted. `check_category_length` skips categories in it.

- [ ] **Step 1: Write the failing tests**

```python
class TestCategoryDelete(IntegrationTestCase):
    def test_deleting_a_subcategory_moves_its_articles_to_the_parent(self): ...
    def test_deleting_a_category_promotes_its_subcategories(self):
        delete_category(parent)
        self.assertIsNone(frappe.db.get_value("HD Article Category", sub, "parent_article_category"))
        self.assertEqual(frappe.db.get_value("HD Article", own_article, "category"), get_general_category())
    def test_deleting_a_subcategory_of_general_keeps_articles_in_general(self): ...
    def test_branch_delete_removes_subcategories_and_articles(self):
        delete_category(parent, delete_articles=True)
        self.assertFalse(frappe.db.exists("HD Article Category", sub))
        self.assertFalse(frappe.db.exists("HD Article", {"name": ["in", branch_articles]}))
    def test_branch_delete_archives_cited_articles(self):
        self.assertEqual(delete_category(parent, delete_articles=True), {"archived": 1})
        self.assertEqual(frappe.db.get_value("HD Article", cited, ["status", "category"]), ("Archived", None))
    def test_deleting_an_article_with_feedback_removes_the_feedback(self): ...  # via delete_articles([name])
    def test_the_summary_counts_the_branch(self):
        self.assertEqual(get_category_delete_summary(parent), {"articles": 3, "subcategories": 1, "cited": 1})
    def test_general_cannot_be_deleted(self): ...
    def test_an_agent_without_delete_permission_is_refused(self): ...  # PermissionError
```

- [ ] **Step 2: Run them and check they fail.** Expected: FAIL.

- [ ] **Step 3: Implement.**
  - `on_trash`, which also runs for the plain `frappe.client.delete`:
    - A Subcategory runs `move_category_articles(self.name, parent)`.
    - A Category clears `parent_article_category` on its Subcategories with `frappe.db.set_value`, before Frappe's link check (it runs after `on_trash`), then moves its own Articles to General.
  - `delete_category(delete_articles=True)`:
    1. Set the flag.
    2. Run `delete_or_archive_article` over every branch Article.
    3. Delete each Subcategory, then the Category.
  - Route `delete_articles` through `delete_or_archive_article`. Its toast count is the caller's concern.

- [ ] **Step 4: Run them and check they pass.** Run the whole module plus `test_hd_article_category`. Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -m "feat(kb): delete a category or its whole branch; archive cited articles"`

---

### Task 6: Merge rules and desk group options (D18, D26)

**Files:**
- Modify: `helpdesk/api/knowledge_base.py` (`merge_category`, new `get_category_group_options`)
- Modify: `helpdesk/api/doc.py` (`get_list_data`: for `doctype == "HD Article"` with `group_by_field == "category"`, return `get_category_group_options(options)` in place of the generic sort)
- Test: `helpdesk/tests/api/test_knowledge_base.py` (class `TestCategoryMerge`), `helpdesk/tests/api/test_doc_list.py`

**Interfaces:**
- Consumes: `get_category_labels` and the sort key (Task 4), `narrow_category_articles` (Task 3).
- Produces: `get_category_group_options(options: list[dict]) -> list[dict]`. It relabels each option with `get_category_labels`, adds `parent_article_category` and `has_subcategories`, and appends an option for every parent whose Subcategories appear when the parent itself has no rows. It sorts with the Task 4 key, and the empty-category option stays last.

- [ ] **Step 1: Write the failing tests**

```python
class TestCategoryMerge(IntegrationTestCase):
    def test_subcategories_follow_into_a_top_level_target(self): ...
    def test_merging_a_parent_into_another_subcategory_is_refused(self): ...  # ValidationError "Move its subcategories first"
    def test_merging_into_its_own_subcategory_promotes_it(self):
        merge_category(parent, sub)
        self.assertIsNone(frappe.db.get_value("HD Article Category", sub, "parent_article_category"))
        self.assertEqual(set(get_subcategories(sub)), {other_sub})
    def test_a_subcategory_merges_into_its_parent(self): ...
    def test_merged_articles_narrow_to_the_target(self): ...

# test_doc_list.py
def test_group_labels_name_the_parent(self): ...   # options for HD Article grouped by category read "Billing › FAQ"
def test_a_parent_with_no_articles_still_gets_a_group(self): ...
def test_subcategory_groups_follow_their_parent(self): ...
```

- [ ] **Step 2: Run them and check they fail.** Expected: FAIL.

- [ ] **Step 3: Implement.**
  - `merge_category`: when the source has Subcategories:
    - If the target is one of them, clear the target's parent first and re-parent the rest to the target.
    - Else, if the target has a parent, throw `_("Move its subcategories first")`.
    - Else, re-parent the Subcategories to the target by saving each one, so the Task 3 narrowing runs.
  - Then run the existing article move and delete.

- [ ] **Step 4: Run them and check they pass.** Run both modules. Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -m "feat(kb): merge subcategories and group the desk list by category › subcategory"`

---

### Task 7: Desk UI (D9, D16, D17, D26, D27)

**Files:**
- Modify: `desk/src/components/knowledge-base/CategoryModal.vue` (adds a "Parent Category" select)
- Modify: `desk/src/components/knowledge-base/MoveToCategoryModal.vue`, `desk/src/components/knowledge-base/MergeCategoryModal.vue` (Link → select fed by `get_category_options`)
- Create: `desk/src/components/knowledge-base/DeleteCategoryModal.vue`
- Modify: `desk/src/pages/knowledge-base/KnowledgeBaseAgent.vue` (`groupByActions`, `handleCategoryDelete`, create and update handlers)
- Modify: `desk/src/stores/knowledgeBase.ts` (resources `categoryOptions`, `categoryDeleteSummary`, `deleteCategory`; `newCategory` passes `parent`)
- Modify: `helpdesk/api/knowledge_base.py` (`create_category(title, icon=None, parent=None)`)
- Test: `helpdesk/tests/api/test_knowledge_base.py` (`test_a_new_subcategory_starts_with_an_article_under_its_parent`)

**Interfaces:**
- Consumes: `get_category_options`, `get_category_delete_summary`, `delete_category`, `create_category(..., parent)`, and group options carrying `parent_article_category` and `has_subcategories`.
- The modal's parent options are the top-level categories minus the category itself. The select is disabled when `has_subcategories` is true. A Subcategory created from a group menu has the parent preset.
- After an update that set a parent, re-read the category's `pinned`. When it was pinned before and is not now, toast `__("{0} is now a subcategory and was unpinned from the knowledge base home", [title])`.

- [ ] **Step 1: Write the failing backend test** for `create_category(title, parent=parent)`: the category's parent is `parent`, and its starter "New Article" sits in it. Run it and check it fails, then make it pass.

- [ ] **Step 2: Build the UI.**
  - `groupByActions`:
    - Add "New subcategory" (`lucide-folder-plus`), shown only when the group has no `parent_article_category`.
    - Replace the `$dialog` in `handleCategoryDelete` with `DeleteCategoryModal`. It loads the summary and shows the "Also delete articles" checkbox, unticked.
      - Unticked message: subcategories become top-level and articles move to General. For a Subcategory: articles move to the parent.
      - Ticked message: `__("Deletes {0} subcategories and {1} articles", [s, a])`, plus `__("{0} articles cited by tickets will be archived", [c])` when `c > 0`.
    - Confirm calls `delete_category`. The success toast names the archived count when it is above 0.

- [ ] **Step 3: Check in the browser** on `e2e.localhost:8020` as an agent, with a Playwright script run from `apps/helpdesk` that uses `e2e/.auth/agent.json`:
  - create a Subcategory from the group menu;
  - re-parent a pinned Category and see the unpin toast;
  - delete a branch with the box ticked and see the counts.

  Expected: each step shows the new group label and order.

- [ ] **Step 4: Run the lint and type checks**

Run: `cd desk && yarn lint` (or the repo's configured check) and `npx vue-tsc --noEmit` if the repo uses it. Expected: no new errors.

- [ ] **Step 5: Commit**

`git commit -m "feat(kb): manage subcategories from the desk"`

---

### Task 8: Portal UI (D19–D25)

**Files:**
- Modify: `studio/helpdesk/studio_page/categories/categories.ts` (`shownCategories` keeps rows without `parent_article_category`)
- Modify: `studio/helpdesk/studio_page/category/category.ts`
  - Adds `subcategories`: sidebar rows whose `parent_article_category` is the current name, sorted by `category_name`.
  - Adds `parentCategory`: the parent's row, or null.
- Modify: `studio/helpdesk/studio_page/category/category.json`
  - A "subcategories" section after `articles-section`, a Repeater of `PortalLink` cards to `/help/category/<name>` with the count, matching `studio_components/category_grid.json`.
  - A breadcrumb in `category-header`: Help › Parent › Subcategory.
- Modify: `studio/helpdesk/studio_page/article/article.ts`
  - `relatedArticles`: the same category first, then the parent's Articles, capped at `RELATED_LIMIT`.
  - Breadcrumb data gains `parentCategory`.
- Modify: `studio/helpdesk/studio_page/article/article.json` (the breadcrumb block)
- Modify: `studio/helpdesk/components/knowledge_base/PortalArticleSidebar.vue`
  - Nests Subcategories under their parent.
  - The current Article's Subcategory and its parent are both open.
  - Search matches nested titles.
- Modify: `studio/helpdesk/components/knowledge_base/PortalArticleSearch.vue` (shows `category_label`)
- Modify: `shared/src/settings/knowledgeBaseDraft.ts` (`categoryOptions` keeps top-level categories only, D9)

**Interfaces:**
- Consumes: sidebar and category rows with `parent_article_category`, `label` and `article_count` (Task 4), and `get_article().category_label`, `parent_article_category`, `parent_category_name`.

- [ ] **Step 1: Build** the changes above, then run `bench build-studio-app helpdesk --site e2e.localhost`.

- [ ] **Step 2: Check in the browser** with a customer (`e2e/.auth/customer.json`) and a guest on a public KB:
  - home lists the parent, not the Subcategory;
  - the parent page shows its Articles, then the Subcategory cards;
  - the breadcrumb reads Help › Parent › Sub;
  - the sidebar nests;
  - search shows `Parent › Sub`.

  Expected: all five hold, and also at 390px width.

- [ ] **Step 3: Commit**

`git commit -m "feat(portal): browse subcategories in the knowledge base"`

---

### Task 9: End-to-end walk (D32)

**Files:**
- Modify: `e2e/tests/knowledge-base/portal-walkthrough.spec.ts` (a new `describe("subcategories")`)
- Modify: `e2e/helpers/factories.ts`, only if it lacks a category factory that takes `parent_article_category`.

- [ ] **Step 1: Write the spec.** Seed over `api` with `uid()` names:
  - a parent with one Customers Article;
  - Subcategory A with one Customers Article;
  - Subcategory B with one Private Article.

  As `usePersona("customer")`, the test:
  1. opens `/help`;
  2. clicks the parent;
  3. sees A's card and not B's;
  4. opens A, then its Article;
  5. asserts the breadcrumb reads `Help`, the parent, then A.

- [ ] **Step 2: Run it.** Serve `e2e.localhost` on :8020 (Global Constraints), then from `apps/helpdesk` run `BASE_URL=http://localhost:8020 SITE_NAME=e2e.localhost npx playwright test e2e/tests/knowledge-base/portal-walkthrough.spec.ts -g subcategories`. Expected: PASS.

- [ ] **Step 3: Run the whole KB e2e folder and the backend KB modules** to catch regressions. Expected: PASS.

- [ ] **Step 4: Commit**

`git commit -m "test(e2e): walk a customer through a subcategory"`
