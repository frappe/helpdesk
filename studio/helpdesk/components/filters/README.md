# Filters

The customer ticket list's filter popover — a port of the desk's
`view-controls`/`conditions-filter` pair, reshaped for the portal.

- `KbFilter.vue` — the popover shell: trigger, two sliding panels
  (field list → value editor), and the transitions between them.
- `KbFilterFieldList.vue` / `KbFilterValueEditor.vue` — the two panels.
  The value editor branches per fieldtype (link search, select, rating,
  date), which is why it is the big one.
- `KbFilterTrigger.vue`, `KbFilterBack.vue`, `KbFilterShortcutKey.vue` —
  small chrome.
- `model.ts` — filter state: `useFilter`, `normalizeFilters` (UI shape ↔
  Frappe's `[field, operator, value]` wire form), link search, summaries.
- `support.ts` — hand-ported `useDebounceFn`/`useEventListener`/
  `useShortcut`/`useDevice`: the studio build resolves only
  vue/vue-router/pinia/frappe-ui/reka-ui/@tiptap for files outside its
  project, so vueuse cannot be imported here.
