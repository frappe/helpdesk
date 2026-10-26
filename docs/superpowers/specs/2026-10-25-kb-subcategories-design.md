# Knowledge base Subcategories: design

Settled in a grilling session on 2026-10-25. Terms are defined in `CONTEXT.md`; the shape and the rejected options are in `docs/adr/0001-one-level-subcategories-with-derived-access.md`.

## Problem

A Category grows too many Articles, and nothing groups related Articles inside it.

## Decisions

### Model

1. One level only: Category › Subcategory. A Subcategory never holds Subcategories.
2. Field `parent_article_category` (Link to HD Article Category, label "Parent Category"). HD Article Category is a Frappe tree (`is_tree`) with `parent_article_category` as its tree parent, so admins get the Tree view at `/app/hd-article-category/view/tree`. The tree stays one level deep: the controller validations refuse a deeper one. `is_group` is 1 for a top-level Category and 0 for a Subcategory. On existing sites, `lft`, `rgt`, `is_group` and `old_parent` hold stale values from the old tree. The patch `hd_article_category_tree` recomputes them from `parent_article_category`. The old `parent_category` column stays untouched.
3. A Category holds Articles and Subcategories. A Subcategory holds Articles only.
4. The "at least one Article" rule applies only to a Category without Subcategories.
5. General can hold Subcategories. General never becomes a Subcategory.
6. A Category becomes a Subcategory, or a Subcategory becomes top-level, by changing its parent. A Category with Subcategories cannot get a parent.
7. The same name may repeat under different parents. Outside its parent, a Subcategory always reads "Category › Subcategory".
8. Subcategories sort alphabetically.
9. A pinned Category that gets a parent is unpinned, and the save says so. Subcategories cannot be pinned.

### Access

10. Access stays on Articles. Category access is read across the Category and its Subcategories, and is Mixed when they differ.
11. A reader sees a Category when they can read any Article in it or in its Subcategories.
12. Setting access on a Category rewrites the Articles of its Subcategories too.
13. Joining narrows access, never widens it. This covers moving Articles into a Category and giving a Category a parent.

### Delete and merge

14. Deleting a Subcategory moves its Articles to its parent.
15. Deleting a Category moves its own Articles to General and makes its Subcategories top-level.
16. The delete dialog has an "Also delete articles" checkbox, unticked by default. Ticked, it deletes the whole branch: the Category, its Subcategories and all their Articles. The dialog states the counts.
17. A deleted Article that a ticket cites (`source_article`) is archived instead, and the toast says so.
18. Merging a Category that has Subcategories:
    - into a top-level target: the Subcategories move under the target.
    - into another Category's Subcategory: refused ("Move its subcategories first").
    - into its own Subcategory: that Subcategory becomes top-level and takes everything.

### Portal

19. The home grid shows top-level Categories only.
20. A Category page lists its own Articles first, then Subcategory cards.
21. The sidebar nests Category › Subcategory › Articles. The open Article expands both levels.
22. Breadcrumb: Help › Category › Subcategory › Article.
23. URLs stay flat: `/help/category/<name>`.
24. A Category's Article count includes its Subcategories, counting only what the reader can read.
25. Related Articles: the same Subcategory first, then filled from its parent.

### Desk

26. The grouped Article list stays. Subcategory groups read "Category › Subcategory" and sort right after their parent. A Category with no Articles of its own still gets a group header.
27. The group menu gains "New subcategory". The category modal gains a "Parent Category" picker. A new Subcategory starts with a "New Article", as a new Category does.

### In this PR, fixes that exist today

28. Archiving the last Article of a Category empties it, because `before_save` clears the category after `validate` checked it.
29. Category access counts Draft Articles. Published Articles decide; a Category with none falls back to every Article.
30. Articles moved by merge or delete keep their old category in the search index. Renaming a Category leaves its old name in the index.
31. Deleting an Article that has feedback or a citing ticket fails on the link check.

### Tests

32. Backend unit tests for every rule above, plus one e2e: a customer walks Help › Category › Subcategory › Article, and a Private Subcategory stays hidden. Run them only on `e2e.localhost`.
