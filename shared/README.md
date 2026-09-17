# @helpdesk/shared

Source shared by the two frontends that render helpdesk data: the agent desk
(`desk/`) and the customer portal, which is a Studio app (`studio/helpdesk/`).
Studio compiles this source in place, so it ships raw `.vue`/`.ts` — there is no
build step.

Two rules keep it consumable from both:

- **No `@/` imports.** Each frontend aliases `@` to its own `src/`, so an alias
  here would resolve differently depending on who compiled it. Relative only.
- **`vue` and `frappe-ui` are peers**, never dependencies — a second copy of
  either breaks reactivity and the editor's plugin keys. `@vueuse/core` is a
  real dependency, because a Studio app has no `node_modules` above it to
  inherit one from.

`~icons/lucide/*` is supplied by the consumer's build (`frappe-ui/vite` with
`lucideIcons: true`). Both frontends enable it.
