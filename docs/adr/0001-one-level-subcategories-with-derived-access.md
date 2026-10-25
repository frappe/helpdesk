# One-level Subcategories with derived access

Large Categories needed splitting into themes, so a Category can hold Subcategories one level deep, linked through a new `parent_article_category` field rather than a tree. Access stays on Articles: a Category's access is derived from the Articles in it and its Subcategories, and a reader sees a Category when they can read any of those Articles.

## Considered Options

- **Any-depth tree** (`is_tree`, nested set): the KB used this until January 2025 and dropped it. One level covers the need without recursive access checks; widening later is easier than collapsing a tree.
- **Stored access on Category**, capping its Articles and Subcategories: a rework of the whole access model, left for a separate project.
- **Reusing `parent_category`**: sites older than January 2025 still hold stale values from the old tree in that column. A new fieldname keeps that data untouched instead of reviving or wiping it.

## Consequences

- A Category with Subcategories may have no Articles of its own, yet still shows to readers of its Subcategories.
- Setting access on a Category rewrites its Subcategories' Articles too, and moving a Category under another narrows its Articles' access, never widens it.
