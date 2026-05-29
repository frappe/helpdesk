# Frappe UI — Design Taste & Patterns

A working reference, mined from `frappe-ui/`, for what to reach for *first* when building UI in apps that consume the library (helpdesk, etc.). Token names are exact; class names are how they appear in templates.

---

## 1. The three color scales

frappe-ui builds everything from three *semantic* scales. The trap is that they don't overlap — each scale has a specific use, and using one in the wrong slot quietly produces nothing.

| Scale | Use it for | Class prefix | Exists in |
|---|---|---|---|
| `surface` | Backgrounds, fill | `bg-surface-*` | gray-1..7, green-1..3, amber-1..2, red-1..6, blue-1..2, cyan-1, orange-1, pink-1, violet-1, plus `cards`, `modal`, `menu-bar`, `selected`, `white` |
| `ink` | Text, SVG fill/stroke | `text-ink-*` | gray-1..9, green-1..3, amber-1..3, red-1..4, blue-1..4, cyan-1, pink-1, violet-1, plus `white` |
| `outline` | Borders, rings | `border-outline-*`, `ring-outline-*` | gray-1..5, gray-modals, green-1..2, amber-1..2, red-1..4, blue-1..2, orange-1, white |

Mismatched scales fail silently. `bg-ink-amber-3` is not a class — nothing renders. Always:
- background → `surface`
- text → `ink`
- border → `outline`

Every token resolves to a CSS variable that flips between `[data-theme]` light and dark. Don't hardcode hex; you'll break dark mode for everyone downstream.

### Gray shade meanings (observed usage)

The numbers are not "lightness levels" you can interpolate between — they have load-bearing roles:

**Backgrounds (`bg-surface-gray-N`)**

| Token | Role |
|---|---|
| `gray-1` | Disabled input fill |
| `gray-2` | **Default subtle fill** (subtle buttons, inputs, hover-resting state on rows). Most-used surface. |
| `gray-3` | Hover state on subtle/ghost elements; "highlighted row" in lists/dropdowns |
| `gray-4` | Active/pressed state |
| `gray-5..6` | Solid button hover state for the `gray` theme |
| `gray-7` | **Solid gray button fill**, tooltip bubble fill, progress-bar filled portion |
| `gray-modals` (outline) | The hairline between rows inside dropdowns/popovers |

Rule of thumb: rest → `gray-2`, hover → `gray-3`, pressed → `gray-4`, "always-prominent" → `gray-7`. If you need something stronger than 7 for a background, you're probably reaching for a different theme.

**Text (`text-ink-gray-N`)**

| Token | Role |
|---|---|
| `gray-4` | Placeholder, disabled label, "least important" metadata |
| `gray-5` | Subtitle / secondary label (e.g. row subtitles, hints) |
| `gray-6` | Body text, dropdown item base color |
| `gray-7` | Default text inside form labels and ItemListRow |
| `gray-8` | Default text inside Buttons / inputs / dialogs |
| `gray-9` | Headings, emphasized labels (selected dropdown title, dialog `<h3>`) |

The most-used is `gray-5`, not `gray-9` — frappe-ui leans toward subdued. When you reach for `gray-9`, you're saying "this is the one important word on the screen."

**Borders (`border-outline-gray-N`)**

| Token | Role |
|---|---|
| `gray-1` | Hairline between badges/outline variants |
| `gray-2` | **Default border** on outline buttons, outline inputs, the kbd shortcut chip |
| `gray-3` | Hover border, focus ring color |
| `gray-4` | Focused/active input border, checkbox base |
| `gray-modals` | Divider inside modals/dropdowns |

---

## 2. Status / semantic colors

frappe-ui ships four "themed" palettes that all components route through identically. Pick the meaning, not the color:

| Theme | What it means | Solid bg | Subtle bg | Ink |
|---|---|---|---|---|
| `gray` | Neutral, default | `surface-gray-7` | `surface-gray-2` | `ink-gray-8` |
| `blue` | Info, primary action | `blue-500` (raw) | `surface-blue-2` | `ink-blue-3` |
| `green` | Success, "OK to proceed" | `surface-green-3` | `surface-green-2` | `ink-green-3` |
| `orange` (Badge) | Warning | `surface-amber-2` | `surface-amber-1` | `ink-amber-3` |
| `red` | Destructive, error | `surface-red-5` (Button) / `red-4` (Badge) | `surface-red-2` | `ink-red-4` |

**Gotcha**: there is **no `surface-amber-3`** — amber surface tops out at `-2`. There *is* `ink-amber-3` (text). Don't transpose them.

**Default theme is `gray-subtle`**: a gray pill on a faintly-gray background. Components reach for color only when meaning demands it.

---

## 3. Typography

Two parallel scales sit in `tokens.js`: a tight one for UI chrome and a relaxed one for prose.

**UI scale** — tight line-height (1.15), heavier letter-spacing (~0.02em), font-weight 420 below `lg`:

```
2xs  11px       xs  12px       sm  13px       base 14px (default)
lg   16px       xl  18px       2xl 20px       3xl  24px
```

**Paragraph scale** — looser line-height (1.5–1.6) for multi-line copy. Same sizes, names prefixed `p-`:

```
p-2xs  p-xs  p-sm  p-base  p-lg  p-xl  p-2xl  p-3xl
```

**The rule**: use `text-p-*` for anything that may wrap to two or more lines (descriptions, ticket bodies, notes). Use the plain `text-*` for single-line UI (buttons, labels, badges, table cells). Mixing wrong gives you cramped descriptions or stretched UI.

**Default size**: `text-base` (14px). Don't think bigger unless it's a heading.

**Weight**: components mostly avoid setting weight explicitly — the font itself ships a low-key default (420 below 16px, 400 above). Use `font-medium` for labels, `font-semibold` for headings, nothing in between.

---

## 4. Sizing system (small / medium / large / xl / 2xl)

Every interactive component shares a `size` prop with the same 5-step scale. The heights are deliberately chosen to align across components so a Button sits next to a TextInput cleanly.

| Component | `sm` | `md` | `lg` | `xl` | `2xl` |
|---|---|---|---|---|---|
| **Button** (default) | h-7, px-2, rounded, text-base | h-8, px-2.5, rounded, font-medium | h-10, px-3, rounded-md, text-lg | h-11.5, px-3.5, rounded-lg, text-xl | h-13, px-3.5, rounded-xl, text-2xl |
| **TextInput** | h-7, rounded, py-1.5, ps-2/8 | h-8, rounded, py-1.5, ps-2.5/9 | h-10, rounded-md, py-1.5, ps-3/10 | h-10, rounded-md | — |
| **Avatar** | w-5 h-5 | w-6 h-6 | w-7 h-7 | w-8 h-8 | w-10 h-10 (`3xl`: w-11.5 h-11.5) |
| **Badge** | h-4, text-xs, px-1.5 | h-5, text-xs, px-1.5 | h-6, text-sm, px-2 | h-7, text-base, px-2 | — |
| **Checkbox** | w-3.5 h-3.5 (input) | w-4 h-4 | — | — | — |
| **ItemListRow** | min-h-7, px-2, py-1.5 | min-h-8, px-2.5, py-1.5 | min-h-10, px-3, py-2 | min-h-10, px-3, py-2 | — |
| **Progress (height)** | h-[2px] | h-1 | h-2 | h-3 | — |
| **Dialog** (`max-w-*`) | xs, sm, md, lg (default), xl, 2xl–7xl |

**Default size everywhere is `sm`** (Button, TextInput, ItemListRow). The library is built for compact dashboards, not consumer-app cushiness. When in doubt, pick `sm`.

**The 7px row** — `h-7` (28px) is the *unit* of the system. Buttons-sm, TextInput-sm, ItemListRow-sm, dropdown group label, "kbd" key chips — all 28px tall. If you're putting controls in a row and they're not all 28px, you'll get vertical misalignment.

**Icon sizes inside controls** — match the control:

| Button size | Icon class |
|---|---|
| sm | `h-4` / `size-4` |
| md | `h-4.5` / `size-4.5` |
| lg | `h-5` / `size-5` |
| xl, 2xl | `h-6` / `size-6` |

Most icons in the wild use **`size-4`** (16px) — frappe-ui counted 50+ uses, vs. ~4 for `size-5`.

---

## 5. Border radius

| Token | Class | Use |
|---|---|---|
| `0px` | `rounded-none` | Tables, very tight grids |
| `4px` | `rounded-sm` | Small chips, kbd key, table cells, tightest tags |
| `8px` (DEFAULT) | `rounded` | **Buttons-sm/md, inputs-sm/md, badges**, default everything |
| `10px` | `rounded-md` | Buttons-lg, inputs-lg, dialog icon container |
| `12px` | `rounded-lg` | **Dropdown / popover bodies, dialogs**, Button-xl, Progress bar track |
| `16px` | `rounded-xl` | Modals, Button-2xl, Progress |
| `20px` | `rounded-2xl` | Rare — large hero containers |
| `9999px` | `rounded-full` | Avatars, dots, status pills, badges (badges are `rounded-full` regardless of size) |

**Pattern**: the radius scales *with* the size, except badges, which are always pill-shaped (`rounded-full`).

Most-used in the codebase: `rounded-lg` (15) > `rounded-md` (12) > `rounded-full` (10) > `rounded-sm` (5).

---

## 6. Shadows

```
sm    →  buttons on hover (focus:shadow-sm), inputs on hover
DEFAULT
md    →  rare
lg    →  rare
xl    →  large floating panels (calendar picker, etc.)
2xl   →  dropdown content, command palette, popover bodies
```

**The two you'll actually use**: `shadow-sm` for "lift on hover" and `shadow-2xl` for floating menus/popovers. Anything in between is usually a tell that you should reconsider.

Floating panels combine `shadow-2xl` with `ring-1 ring-black ring-opacity-5` — that ring + shadow combo is the dropdown signature. Reuse `dropdownClasses.content` from `src/components/Dropdown/utils.ts` rather than recreating it:

```ts
'dropdown-content min-w-40 divide-y divide-outline-gray-modals
 rounded-lg bg-surface-modal shadow-2xl
 ring-1 ring-black ring-opacity-5 focus:outline-none'
```

---

## 7. Spacing

frappe-ui is consistent about which spacing tokens it uses. Counts from the components folder:

**Gap (most common):**
- `gap-2` (8px) — overwhelmingly the default — used between sibling controls, label+icon, prefix+content
- `gap-1` (4px) — tight pairs (icon + small text, inside a Badge)
- `gap-1.5` (6px) — uncommon but appears between rows in dense lists
- `gap-3` / `gap-4` — between distinct logical groups in a header

**Padding (component-internal):**
- `p-1.5` — dropdown group inset
- `px-2 py-1.5` — default item row (matches the `h-7` rhythm)
- `px-2.5 py-1.5` — medium row
- `px-3 py-2` — large row

**Pattern recognition cheat**: when laying out a row of controls, default to `gap-2`. When the controls touch (a search box with an inline x-button), drop to `gap-1`. When the row has distinct sections, go to `gap-3`/`gap-4`. There's almost never a reason for `gap-5`/`gap-6`.

**Vertical spacing** — for multi-line inputs/forms, `space-y-1.5` between label and control is the default (`LabelingWrapper` enforces this).

---

## 8. Variants

Every "themable" component (Button, Badge, Alert, Input) supports the same four variants:

| Variant | Use when | Visual |
|---|---|---|
| `subtle` | **Default**. Pill on a faint colored ground. Most buttons in the app. | bg-`surface-X-2`, text-`ink-X-3` |
| `solid` | Primary action, only one per surface | bg-`surface-X-3..7`, text-`ink-white` |
| `outline` | Secondary action; "important but not the primary" | bg-`surface-white`, border-`outline-X-1..2` |
| `ghost` | Toolbar icons, hover-revealed actions | bg-transparent, hover → `surface-X-2/3` |

**Selection rule for buttons**: one `solid` per region (the "Assign" / "Send" / "Save"). The "Cancel" is `outline`. Toolbar icons (kebab, close) are `ghost`. Everything else is `subtle`.

**Disabled** is computed from `theme-variant` pairs — Button has 16 distinct disabled mappings. Just pass `disabled` and trust the component; don't override.

---

## 9. Focus & accessibility patterns

Two layered focus styles, used together:

```
focus:outline-none                       — strip the browser default
focus-visible:ring focus-visible:ring-outline-gray-3
focus-visible:ring-2                     — focus ring only when keyboard navigating
```

For colored themes, the ring color matches: `ring-outline-green-2` / `ring-outline-red-2`, etc. `focus-visible` (not `focus`) is the rule — mouse clicks should not show a focus ring.

Every interactive component sets `aria-label` (icon-only Button), `aria-invalid` + `aria-errormessage` (Input), `role="progressbar"` (Progress), `aria-valuemax/min/now` (Progress). Mirror that pattern in app code.

---

## 10. Component patterns worth memorizing

### Floating bodies (dropdown, popover, command palette)

```html
<div class="my-2 rounded-lg bg-surface-modal shadow-2xl
            ring-1 ring-black ring-opacity-5 focus:outline-none
            divide-y divide-outline-gray-modals">
  <section class="p-1.5">...</section>   <!-- group -->
  <section class="p-1.5">...</section>   <!-- next group -->
</div>
```

The `divide-y divide-outline-gray-modals` between groups is the visual signature. `my-2` gives breathing room from the trigger.

### Row-with-side-info (list item, dropdown item, settings row)

```
[ avatar ]  [ flex-1 truncate ]  [ side label ]  [ kebab ]
   shrink-0       min-w-0           shrink-0      shrink-0
```

`min-w-0` on the flex-1 child is *required* for `truncate` to work — without it the child refuses to shrink. `shrink-0` on the bookends keeps icons from squashing.

### Pill of dot + text

```html
<span class="size-1.5 rounded-full" :class="statusColor(value)" />
<span class="text-p-sm text-ink-gray-7">{{ value }}</span>
```

`size-1.5` (6px) dot for status indicators; `size-2` (8px) only when it needs to read as a discrete element.

### Keyboard chip

```html
<kbd class="bg-surface-gray-2 border border-outline-gray-2
            text-xs rounded-sm text-ink-gray-8 shadow-sm
            min-w-5 h-5 flex items-center justify-center w-5">⌘</kbd>
```

Square, `h-5 min-w-5`, `rounded-sm`. Used inside footer hints and the shortcuts modal.

### Form label + control

```html
<LabelingWrapper class="space-y-1.5">
  <InputLabel class="text-p-sm font-medium text-ink-gray-7" />
  <input class="h-7 rounded bg-surface-gray-2 placeholder-ink-gray-4
                focus:bg-surface-white focus:border-outline-gray-4 ..." />
</LabelingWrapper>
```

`space-y-1.5` (6px) between label and field. Labels are `text-p-sm font-medium text-ink-gray-7` — *paragraph*-sm (not UI-sm) because labels are content, not chrome.

---

## 11. Conventions that bite

1. **Don't write raw color shades.** No `bg-gray-200`, `text-red-600`, `border-blue-500`. The whole point of the three scales is to keep dark mode working — raw shades skip the variable layer.
2. **`text-ink-*` never works as a background, `bg-surface-*` never works as text.** They share names (`amber-3`) but exist in different scales. The component will look unstyled if you cross them.
3. **Default theme is `gray-subtle`.** When you pick a non-gray theme, you're communicating *something*. Use it intentionally.
4. **Default size is `sm`.** Components scale down by default, not up. Reach for `md`/`lg` only when the surface genuinely demands more presence.
5. **Use the `size` prop, not custom heights.** Setting `h-9` on a Button breaks the 28-32-40 rhythm and the icon-sizing computed.
6. **`text-p-*` for prose, `text-*` for UI.** Don't put a button label in `text-p-base` — line-height is wrong.
7. **`size-4` (16px) is the icon default.** Use `size-3.5`/`size-5` only when the surrounding control demands it.
8. **`gap-2` is the default gap.** Pick something else when you have a reason, not by default.
9. **Buttons get one `solid` per region.** Two solid buttons next to each other dilutes the primary.
10. **Don't recreate dropdown styling.** Import `dropdownClasses.content` from `Dropdown/utils.ts`.

---

## 12. Quick lookup — "I want to make…"

| You want to make… | Reach for |
|---|---|
| A button that looks like every other button | `<Button>` with no props (= gray-subtle-sm) |
| The "primary" button in a footer | `<Button variant="solid">` (theme stays gray unless it's destructive/positive) |
| A destructive button | `<Button variant="subtle" theme="red">` (or `solid` for confirm dialogs) |
| A pill that says "Active" | `<Badge :label="'Active'" theme="green" variant="subtle">` |
| A floating menu | `<Dropdown>` — body styling is automatic via `dropdownClasses.content` |
| An input | `<TextInput>` (size `sm`, variant `subtle` by default) |
| A modal | `<Dialog size="lg">` (default), or `size="md"` for confirm-style |
| A user avatar | `<Avatar size="md" :image="..." :label="..." />` |
| A status dot | `<span class="size-1.5 rounded-full" :class="statusColor(value)" />` (helpdesk-local) |
| A keyboard shortcut chip | See §10 — `kbd` with `h-5 min-w-5 rounded-sm bg-surface-gray-2 border border-outline-gray-2` |
| A loading state | `<LoadingIndicator>` (sizes match Button) |
| A faint divider | `<hr>` (picks up `border-outline-gray-modals` from theme defaults) or `divide-y divide-outline-gray-modals` |
| A subtle label above content | `<span class="text-p-sm font-medium text-ink-gray-7">` |
| Secondary metadata under a title | `<span class="text-p-sm text-ink-gray-5">` |

---

## 13. Files to read when you need the canonical answer

- `frappe-ui/tailwind/tokens.js` — sizes, radii, shadows, type scale
- `frappe-ui/tailwind/colors.js` — every `--surface-*`, `--text-ink-*`, `--outline-*` definition (light + dark)
- `frappe-ui/src/components/Button/Button.vue` — full size + theme + variant + state matrix
- `frappe-ui/src/components/Badge/Badge.vue` — palette per theme/variant
- `frappe-ui/src/components/TextInput/TextInput.vue` — input chrome and focus pattern
- `frappe-ui/src/components/Dropdown/utils.ts` — the canonical dropdown classes
- `frappe-ui/src/components/ItemListRow/ItemListRow.vue` — the canonical clickable row

When in doubt, grep these for the token you need before inventing one.
