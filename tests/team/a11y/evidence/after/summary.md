# Accessibility scan: after

Run 2026-11-17T17:11:25.507Z against http://127.0.0.1:8000.

| Screen | Use case | Lighthouse a11y | Best practices | SEO | axe rules violated | axe elements |
|---|---|---|---|---|---|---|
| Customer: New Ticket form | UC-01 | 94 | 100 | 100 | 6 | 9 |
| Customer: ticket page (resolved) | UC-02, UC-05 | 100 | 100 | 100 | 0 | 0 |
| Customer: Rate this ticket dialog | UC-02 | - | - | - | 0 | 0 |
| Customer: ticket list | UC-06 | 85 | 100 | 100 | 6 | 8 |
| Agent: ticket page | UC-03, UC-04 | 85 | 100 | 100 | 7 | 45 |

## Customer: New Ticket form

| Tool | Rule / audit | Impact / category | Elements |
|---|---|---|---|
| axe | aria-input-field-name: ARIA input fields must have an accessible name | serious | .tiptap |
| axe | button-name: Buttons must have discernible text | critical | .mr-2.bg-transparent.active\:bg-surface-gray-4 |
| axe | color-contrast: Elements must meet minimum color contrast ratio thresholds | serious | .hover\:text-ink-gray-7 > span |
| axe | landmark-one-main: Document should have one main landmark | moderate | html |
| axe | page-has-heading-one: Page should contain a level-one heading | moderate | html |
| axe | region: All page content should be contained by landmarks | moderate | .gap-5.flex-col.flex > .flex-col.gap-2.flex<br>.p-3 > .text-base<br>.-mx-3<br>.text-sm-medium |
| lighthouse | color-contrast: Background and foreground colors do not have a sufficient contrast ratio. | accessibility | div.flex > div.flex > a.flex > span<br>div.flex > div.flex > div > h4.text-p-sm |
| lighthouse | landmark-one-main: Document does not have a main landmark. | accessibility | html |
| lighthouse | valid-source-maps: Missing source maps for large first-party JavaScript | best-practices |  |

## Customer: ticket page (resolved)

| Tool | Rule / audit | Impact / category | Elements |
|---|---|---|---|
| lighthouse | valid-source-maps: Missing source maps for large first-party JavaScript | best-practices |  |

## Customer: Rate this ticket dialog

| Tool | Rule / audit | Impact / category | Elements |
|---|---|---|---|

## Customer: ticket list

| Tool | Rule / audit | Impact / category | Elements |
|---|---|---|---|
| axe | aria-allowed-attr: Elements must only use supported ARIA attributes | critical | #reka-popover-trigger-v-0-0-6<br>#reka-popover-trigger-v-0-0-9 |
| axe | button-name: Buttons must have discernible text | critical | .rounded-e-none.border-e.active\:bg-surface-gray-4 |
| axe | label-content-name-mismatch: Elements must have their visible text as part of their accessible name | serious | button[aria-label="Filter"] |
| axe | landmark-one-main: Document should have one main landmark | moderate | html |
| axe | page-has-heading-one: Page should contain a level-one heading | moderate | html |
| axe | region: All page content should be contained by landmarks | moderate | .quick-filters<br>.gap-0\.5.flex-col.justify-center |
| lighthouse | aria-allowed-attr: `[aria-*]` attributes do not match their roles | accessibility | div.z-0 > div.flex > div.flex > div#reka-popover-trigger-v-0-0-6<br>div.z-0 > div.flex > div.flex > div#reka-popover-trigger-v-0-0-9 |
| lighthouse | button-name: Buttons do not have an accessible name | accessibility | div.flex > div.flex > div#reka-popover-trigger-v-0-0-9 > button.rounded-e-none |
| lighthouse | landmark-one-main: Document does not have a main landmark. | accessibility | html |
| lighthouse | label-content-name-mismatch: Elements with visible text labels do not have matching accessible names. | accessibility | div.flex > div#reka-popover-trigger-v-0-0-6 > div.flex > button.rounded-e-none |
| lighthouse | valid-source-maps: Missing source maps for large first-party JavaScript | best-practices |  |

## Agent: ticket page

| Tool | Rule / audit | Impact / category | Elements |
|---|---|---|---|
| axe | aria-allowed-attr: Elements must only use supported ARIA attributes | critical | #reka-popover-trigger-v-0-0-61<br>#reka-popover-trigger-v-0-0-72 |
| axe | button-name: Buttons must have discernible text | critical | #reka-dropdown-menu-trigger-v-0-0-2<br>#reka-dropdown-menu-trigger-v-0-0-3<br>#reka-dropdown-menu-trigger-v-0-0-4<br>#reka-dropdown-menu-trigger-v-0-0-5 (+3) |
| axe | color-contrast: Elements must meet minimum color contrast ratio thresholds | serious | .leading-snug<br>a > span<br>#reka-tabs-v-0-0-10-trigger-email > .box-border.transition-\[background-color\,color\,box-shadow\].ease-out > .truncate.min-w-0<br>#reka-tabs-v-0-0-10-trigger-comment > .box-border.transition-\[background-color\,color\,box-shadow\].ease-out > .truncate.min-w-0 (+11) |
| axe | landmark-one-main: Document should have one main landmark | moderate | html |
| axe | landmark-unique: Landmarks should have a unique role or role/label/title (i.e. accessible name) combination | moderate | div[data-reka-scroll-area-viewport=""] > div > nav:nth-child(1) |
| axe | page-has-heading-one: Page should contain a level-one heading | moderate | html |
| axe | region: All page content should be contained by landmarks | moderate | .box-border.transition-\[background-color\,color\,box-shadow\][data-state="active"] > .truncate.min-w-0<br>#reka-tabs-v-0-0-10-trigger-email > .box-border.transition-\[background-color\,color\,box-shadow\].ease-out > .truncate.min-w-0<br>#reka-tabs-v-0-0-10-trigger-comment > .box-border.transition-\[background-color\,color\,box-shadow\].ease-out > .truncate.min-w-0<br>#reka-tabs-v-0-0-10-trigger-analytics > .box-border.transition-\[background-color\,color\,box-shadow\].ease-out > .truncate.min-w-0 (+14) |
| lighthouse | aria-allowed-attr: `[aria-*]` attributes do not match their roles | accessibility | div.space-y-2.5 > div.flex > div.-m-1 > div#reka-popover-trigger-v-0-0-55<br>div.space-y-2.5 > div.flex > div.min-w-0 > div#reka-popover-trigger-v-0-0-58 |
| lighthouse | button-name: Buttons do not have an accessible name | accessibility | nav.flex > div.group/sidebar-item > div.flex > button#reka-dropdown-menu-trigger-v-0-0-2<br>nav.flex > div.group/sidebar-item > div.flex > button#reka-dropdown-menu-trigger-v-0-0-3<br>nav.flex > div.group/sidebar-item > div.flex > button#reka-dropdown-menu-trigger-v-0-0-4<br>nav.flex > div.group/sidebar-item > div.flex > button#reka-dropdown-menu-trigger-v-0-0-5 |
| lighthouse | color-contrast: Background and foreground colors do not have a sufficient contrast ratio. | accessibility | div.relative > h3.text-base > span.flex > span.truncate<br>div.flex > div.flex > a.flex > span<br>div.relative > button#reka-tabs-v-0-0-10-trigger-email > span.inline-flex > span.min-w-0<br>div.relative > button#reka-tabs-v-0-0-10-trigger-comment > span.inline-flex > span.min-w-0 |
| lighthouse | landmark-one-main: Document does not have a main landmark. | accessibility | html |
| lighthouse | valid-source-maps: Missing source maps for large first-party JavaScript | best-practices |  |
