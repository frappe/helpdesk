# One-level Subcategories with derived access

Large Categories needed splitting into themes, so a Category can hold Subcategories one level deep, linked through a new `parent_article_category` field. Access stays on Articles: a Category's access is derived from the Articles in it and its Subcategories, and a reader sees a Category when they can read any of those Articles.

## Considered Options

- **Any-depth tree**: the KB used this until January 2025 and dropped it. One level covers the need without recursive access checks; widening later is easier than collapsing a tree.
- **Stored access on Category**, capping its Articles and Subcategories: a rework of the whole access model, left for a separate project.
- **Reusing `parent_category`**: sites older than January 2025 still hold stale values from the old tree in that column. A new fieldname keeps that data untouched instead of reviving or wiping it.

## Frappe tree, one level deep

HD Article Category is a Frappe tree (`is_tree`, nested set) with `parent_article_category` as the tree parent. Admins wanted Frappe's Tree view to see and edit the Categories. A Frappe tree allows any depth, but the controller validations still refuse a Subcategory of a Subcategory, so the tree stays one level deep. A patch recomputes the stale `lft`, `rgt`, `is_group` and `old_parent` values that older sites keep from the old tree.

## Consequences

- A Category with Subcategories may have no Articles of its own, yet still shows to readers of its Subcategories.
- Setting access on a Category rewrites its Subcategories' Articles too, and moving a Category under another narrows its Articles' access, never widens it.
