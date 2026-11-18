# Accessibility scan: before

Run 2026-11-17T17:07:57.689Z against http://127.0.0.1:8000.

| Screen | Use case | Lighthouse a11y | Best practices | SEO | axe rules violated | axe elements |
|---|---|---|---|---|---|---|
| Customer: New Ticket form | UC-01 | 94 | 100 | 90 | 6 | 9 |
| Customer: ticket page (resolved) | UC-02, UC-05 | 82 | 100 | 90 | 6 | 36 |
| Customer: Rate this ticket dialog | UC-02 | - | - | - | 1 | 9 |
| Customer: ticket list | UC-06 | 85 | 100 | 90 | 6 | 8 |
| Agent: ticket page | UC-03, UC-04 | 85 | 100 | 90 | 7 | 45 |

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
| lighthouse | meta-description: Document does not have a meta description | seo |  |

## Customer: ticket page (resolved)

| Tool | Rule / audit | Impact / category | Elements |
|---|---|---|---|
| axe | button-name: Buttons must have discernible text | critical | .active\:bg-surface-gray-4.w-7.hover\:bg-surface-gray-3 |
| axe | color-contrast: Elements must meet minimum color contrast ratio thresholds | serious | .hover\:text-ink-gray-7 > span<br>div[sender-image="customer.a@sqe.test"] > .mb-4.justify-between.text-base > .gap-0\.5.items-center.flex > span[data-grace-area-trigger=""][data-slot="trigger"][data-state="closed"]<br>div[sender-image="agent.one@sqe.test"] > .mb-4.justify-between.text-base > .gap-0\.5.items-center.flex > span[data-grace-area-trigger=""][data-slot="trigger"][data-state="closed"]<br>.pt-0.py-3.border-b > .leading-5.text-base.items-center:nth-child(2) > .w-\[126px\].text-sm.text-ink-gray-5 (+5) |
| axe | frame-title: Frames must have an accessible name | serious | div[sender-image="customer.a@sqe.test"] > iframe<br>div[sender-image="agent.one@sqe.test"] > iframe |
| axe | landmark-one-main: Document should have one main landmark | moderate | html<br>div[sender-image="customer.a@sqe.test"] > iframe html<br>div[sender-image="agent.one@sqe.test"] > iframe html |
| axe | page-has-heading-one: Page should contain a level-one heading | moderate | html<br>div[sender-image="customer.a@sqe.test"] > iframe html<br>div[sender-image="agent.one@sqe.test"] > iframe html |
| axe | region: All page content should be contained by landmarks | moderate | .mx-6<br>.after\:h-full<br>div[email="customer.a@sqe.test"]<br>div[sender-image="customer.a@sqe.test"] > .mb-4.justify-between.text-base > .gap-0\.5.items-center.flex > span[data-grace-area-trigger=""][data-slot="trigger"][data-state="closed"] (+14) |
| lighthouse | button-name: Buttons do not have an accessible name | accessibility | div.flex > div.flex > div.flex > button.h-7 |
| lighthouse | color-contrast: Background and foreground colors do not have a sufficient contrast ratio. | accessibility | div.flex > div.flex > a.flex > span<br>div.border > div.mb-4 > div.flex > span.text-ink-gray-5<br>div.border > div.mb-4 > div.flex > span.text-ink-gray-5<br>div.flex > div.flex > div.flex > span.w-[126px] |
| lighthouse | frame-title: `<frame>` or `<iframe>` elements do not have a title | accessibility | div#opvf2psn1e > div.w-full > div.border > iframe.prose-f<br>div#oq4uceffhh > div.w-full > div.border > iframe.prose-f |
| lighthouse | landmark-one-main: Document does not have a main landmark. | accessibility | html |
| lighthouse | valid-source-maps: Missing source maps for large first-party JavaScript | best-practices |  |
| lighthouse | meta-description: Document does not have a meta description | seo |  |

## Customer: Rate this ticket dialog

| Tool | Rule / audit | Impact / category | Elements |
|---|---|---|---|
| axe | color-contrast: Elements must meet minimum color contrast ratio thresholds | serious | .hover\:text-ink-gray-7 > span<br>div[sender-image="customer.a@sqe.test"] > .mb-4.justify-between.text-base > .gap-0\.5.items-center.flex > span[data-grace-area-trigger=""][data-slot="trigger"][data-state="closed"]<br>div[sender-image="agent.one@sqe.test"] > .mb-4.justify-between.text-base > .gap-0\.5.items-center.flex > span[data-grace-area-trigger=""][data-slot="trigger"][data-state="closed"]<br>.pt-0.py-3.border-b > .leading-5.text-base.items-center:nth-child(2) > .w-\[126px\].text-sm.text-ink-gray-5 (+5) |

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
| lighthouse | meta-description: Document does not have a meta description | seo |  |

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
| lighthouse | aria-allowed-attr: `[aria-*]` attributes do not match their roles | accessibility | div.space-y-2.5 > div.flex > div.-m-1 > div#reka-popover-trigger-v-0-0-55<br>div.space-y-2.5 > div.flex > div.min-w-0 > div#reka-popover-trigger-v-0-0-66 |
| lighthouse | button-name: Buttons do not have an accessible name | accessibility | nav.flex > div.group/sidebar-item > div.flex > button#reka-dropdown-menu-trigger-v-0-0-2<br>nav.flex > div.group/sidebar-item > div.flex > button#reka-dropdown-menu-trigger-v-0-0-3<br>nav.flex > div.group/sidebar-item > div.flex > button#reka-dropdown-menu-trigger-v-0-0-4<br>nav.flex > div.group/sidebar-item > div.flex > button#reka-dropdown-menu-trigger-v-0-0-5 |
| lighthouse | color-contrast: Background and foreground colors do not have a sufficient contrast ratio. | accessibility | div.relative > h3.text-base > span.flex > span.truncate<br>div.flex > div.flex > a.flex > span<br>div.relative > button#reka-tabs-v-0-0-10-trigger-email > span.inline-flex > span.min-w-0<br>div.relative > button#reka-tabs-v-0-0-10-trigger-comment > span.inline-flex > span.min-w-0 |
| lighthouse | landmark-one-main: Document does not have a main landmark. | accessibility | html |
| lighthouse | valid-source-maps: Missing source maps for large first-party JavaScript | best-practices |  |
| lighthouse | meta-description: Document does not have a meta description | seo |  |
