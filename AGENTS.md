# Copilot Instructions for Frappe Helpdesk

## Project Overview

Frappe Helpdesk is an open-source ticket management tool built on the [Frappe Framework](https://github.com/frappe/frappe) (Python backend) and [Frappe UI](https://github.com/frappe/frappe-ui) (Vue.js frontend). It provides agent/customer portals, SLAs, assignment rules, a knowledge base, and canned responses.

## Tech Stack & Architecture

- **Backend**: Frappe Framework with Python
- **Frontend**: Vue 3 + TypeScript SPA with Vite dev server
- **Database**: MariaDB with structured doctypes
- **Real-time**: WebSockets via Socket.IO for live updates
- **UI Library**: frappe-ui for consistent design components
- **Styling**: Tailwind CSS with semantic design tokens

## Architecture

- **Backend (Python):** Located in `helpdesk/`.
  - API endpoints: `helpdesk/api/`
  - Business logic: `helpdesk/utils.py`, `helpdesk/search.py`, etc.
  - Extensibility: `helpdesk/extends/`, `helpdesk/overrides/`
- **Frontend (Vue.js):** Located in `desk/`.
  - Main entry: `desk/src/main.js`, `desk/src/App.vue`
  - Components: `desk/src/components/`
  - State: `desk/src/stores/`
  - Routing: `desk/src/router/`
  - Styles: Tailwind via `desk/index.css`, config in `desk/tailwind.config.js`

# Frontend: Vue 3 Development Standards

## Frontend Project Context

- `desk/src/` contains the main Vue 3 frontend source code
- Vue 3.x with Composition API as default approach
- TypeScript for type safety and better development experience
- Single File Components (`.vue`) with `<script setup lang="ts">` syntax preferred
- Vite as the build tool for fast development and optimized builds
- Pinia for state management (unlike gameplan which avoids state libraries)
- frappe-ui for UI components and data fetching utilities

## Development Standards

### Architecture & Component Design

- Favor the Composition API (`setup` functions and composables) over the Options API
- Organize components and composables by feature or domain for scalability
- Separate UI-focused components (presentational) from logic-focused components (containers)
- Use PascalCase for component names and file names
- Keep components small and focused on one concern
- Use `<script setup lang="ts">` syntax for brevity and performance
- Favor slots and scoped slots for flexible composition

### TypeScript Integration

- TypeScript is enabled but not in strict mode (as per actual tsconfig.json)
- Use `<script setup lang="ts">` with `defineProps` and `defineEmits`
- Leverage `PropType<T>` for typed props and default values
- Use interfaces or type aliases for complex prop and state shapes
- Define types for event handlers, refs, and `useRoute`/`useRouter` hooks

### Styling Guidelines

- Always prefer Tailwind CSS for styling
- Use utility classes for layout and spacing
- Use semantic class names wherever possible:
  - Background colors: `bg-surface-white`, `bg-surface-gray-1` through `bg-surface-gray-9`, `bg-surface-black`
  - Text colors: `text-ink-white`, `text-ink-gray-1` through `text-ink-gray-9`, `text-ink-black`
  - Fill colors: `fill-ink-*`
  - Placeholder colors: `placeholder-ink-*`
  - Border colors: `border-outline-white`, `border-outline-gray-1` through `border-outline-gray-5`, `border-outline-black`
  - Font sizes: `text-xs`, `text-sm`, `text-base`, `text-lg`, `text-xl`, `text-2xl`, `text-3xl`
  - Multiline text: `text-p-xs`, `text-p-sm`, `text-p-base`, `text-p-lg`, `text-p-xl`, `text-p-2xl`
- Always use gray shades for everything, never use color shades even for primary states
- Implement mobile-first, responsive design with CSS Grid and Flexbox
- Ensure styles are accessible (contrast, focus states)

### Data Fetching with frappe-ui

- Use `createResource`, `createListResource`, and `createDocumentResource` from frappe-ui for data fetching
- Handle loading, error, and success states explicitly
- These are the older but stable composables used throughout the project

When working with a list of documents:

```ts
const tickets = createListResource({
  doctype: "HD Ticket",
  filters: { status: "Open" },
  fields: ["name", "subject", "modified"],
  limit: 20,
  auto: true,
});

// Access data
tickets.data; // Array of ticket objects
tickets.loading; // Boolean loading state
tickets.error; // Error object if any

// Operations
tickets.reload(); // Refresh the list
tickets.update({ name: "<id>", subject: "Updated Subject" }); // Update item
tickets.insert({ subject: "New Ticket" }); // Add new item
tickets.delete("<id>"); // Delete item
```

When working with a single document:

```ts
const ticket = createDocumentResource({
  doctype: "HD Ticket",
  name: "<ticket-id>",
  auto: true,
});

// Access data
ticket.doc; // Document object
ticket.loading; // Boolean loading state
ticket.error; // Error object if any

// Operations
ticket.get(); // Fetch/refresh document
ticket.setValue("status", "Resolved"); // Update field
ticket.save(); // Save changes
ticket.delete(); // Delete document
```

For API calls:

```ts
const apiCall = createResource({
  url: "helpdesk.api.ticket.assign_ticket_to_agent",
  onSuccess(data) {
    // Handle success
  },
  onError(error) {
    // Handle error
  },
});

// Make the call
apiCall.submit({ ticket_id: "<id>", agent_id: "<agent>" });
```

### Icons

- **Primary icon system**: Lucide icons via unplugin-icons for consistency and modern design
- **Secondary**: FeatherIcon component from frappe-ui (legacy usage, prefer Lucide for new components)
- Use Lucide icons for all new components:
  ```vue
  <template>
    <LucidePlus class="size-4" />
  </template>
  ```
- For script usage, import Lucide icons like this:
  ```ts
  import LucidePlus from "~icons/lucide/plus";
  import LucideTicket from "~icons/lucide/ticket";
  ```
- Only use FeatherIcon for maintaining existing components:
  ```vue
  <template>
    <FeatherIcon name="plus" class="h-4 w-4" />
  </template>
  ```

### State Management

- Use Pinia stores for complex shared state
- For simple local state, use `ref` and `reactive` within `setup`
- Use `computed` for derived state
- Keep state normalized for complex structures

### Performance & Accessibility

- Apply `v-once` and `v-memo` for static or infrequently changing elements
- Avoid unnecessary watchers; prefer `computed` where possible
- Use semantic HTML elements and ARIA attributes
- Manage focus for modals and dynamic content
- Ensure keyboard navigation for interactive components

# Backend: Frappe Framework Development Standards

## Backend Project Context

- Frappe Framework provides full-stack capabilities with ORM, permissions, and background jobs
- MariaDB database with structured DocTypes for business entities
- Redis for background workers and caching
- Socket.IO for real-time updates

## Critical Development Workflows

**Local Development Setup**:

- Backend runs via `bench start` from frappe-bench directory
- Python web server: Assume server is already started on port 8000
- Frontend dev server: `cd desk && yarn dev` (typically runs on port 8080)
- Site-specific commands: `bench --site helpdesk.test <command>`

**Data Query Patterns**:

- Always prefer `frappe.qb.get_query()` over `frappe.db.get_all()` for new code
- Use `frappe.qb.get_query(..., ignore_permissions=False)` when permission checks are needed
- Example query patterns from helpdesk context

**Debugging Workflow**:

- Create debug files like `./helpdesk/debug.py` with `def execute():` function
- Run with `bench --site helpdesk.test execute helpdesk.debug.execute`
- Use `print()` statements for console output during debugging

## DocType Architecture Patterns

- Follow Frappe's DocType conventions for business entities
- Implement custom permission logic in `has_permission` hooks
- Use proper field types and validation in DocType definitions
- Leverage DocType methods for business logic encapsulation

## Conventions & Patterns

- **API Design:** Python modules in `helpdesk/api/` follow RESTful patterns. Extend via `helpdesk/extends/`.
- **Frontend:** Vue 3 + Vite with TypeScript. Use Pinia for state management. Components auto-imported via `desk/components.d.ts`.
- **Testing:** Follow Frappe's conventions for backend tests.
- **Localization:** Add translations in `helpdesk/locale/`.
- **Custom Logic:** Use `helpdesk/overrides/` for customizations.

## Utilities and Composables

- @vueuse/core is available for common Vue utilities
- Prefer vueuse composables over custom implementations where applicable
- Common composables: `useLocalStorage`, `useDebounce`, `useElementSize`
- Always use frappe-ui's data fetching composables (`createResource`, `createListResource`, `createDocumentResource`), never `useFetch`

## Error Handling & Forms

- Use global error handlers for uncaught errors
- Wrap risky logic in `try/catch` with user-friendly messages
- Build forms with controlled `v-model` bindings
- Validate on blur or input with debouncing for performance
- Ensure accessible labeling and error announcements

## Integration Points

- **Frappe Framework:** All backend logic integrates with Frappe ORM, permissions, and hooks (`helpdesk/hooks.py`).
- **Frappe UI:** Frontend uses Frappe UI for consistent design components and data fetching.
- **Real-time Updates:** WebSockets via Socket.IO for live ticket updates.
- **Crowdin:** Translation sync via `crowdin.yml`.

## Examples

### Adding a New API Endpoint

1. Create a Python file in `helpdesk/api/`
2. Add `@frappe.whitelist()` decorator to functions
3. Register in `helpdesk/hooks.py` if needed
4. Use `frappe.qb.get_query()` for database queries

### Adding a Frontend Component

1. Create Vue component in `desk/src/components/` or `desk/src/pages/`
2. Use `<script setup lang="ts">` syntax
3. Follow Tailwind semantic class conventions
4. Use frappe-ui composables for data fetching
5. Add route in `desk/src/router/` if it's a page component

### Styling Example

```vue
<template>
  <div class="bg-surface-white border border-outline-gray-2 rounded-lg p-4">
    <h2 class="text-lg text-ink-gray-9 font-semibold mb-2">Ticket Details</h2>
    <p class="text-p-sm text-ink-gray-7">{{ ticket.doc.subject }}</p>
    <LucideTicket class="size-4 text-ink-gray-6" />
  </div>
</template>

<script setup lang="ts">
import { createDocumentResource } from "frappe-ui";
import LucideTicket from "~icons/lucide/ticket";

const ticket = createDocumentResource({
  doctype: "HD Ticket",
  name: props.ticketId,
  auto: true,
});
</script>
```

## Key Files & Directories

### Backend

- `helpdesk/api/` — Backend API endpoints with @frappe.whitelist() decorators
- `helpdesk/utils.py` — Shared backend utilities and helper functions
- `helpdesk/hooks.py` — Frappe hooks
- `helpdesk/overrides/` — Custom logic and extensions

### Frontend

- `desk/src/` — Main Vue 3 frontend source code
- `desk/src/components/` — Reusable Vue components
- `desk/src/pages/` — Page-level components and routes
- `desk/src/stores/` — Pinia stores for state management
- `desk/tailwind.config.js` — Tailwind CSS configuration with semantic tokens
- `desk/components.d.ts` — Auto-generated component type definitions

### Development

- `docker/` — Docker setup for containerized development

## Code Quality & Standards

- Follow Vue's official style guide and best practices
- Use ESLint with Vue 3 recommended rules and Prettier for consistency
- Write meaningful commit messages and maintain clean git history
- Document complex logic with JSDoc/TSDoc comments
- Only add comments that explain why something is done, not what is done
- Keep dependencies updated and audit for security vulnerabilities

## References

- [README.md](../README.md) — Full setup and feature list
- [Frappe Docs](https://frappeframework.com/docs/) — Framework documentation
- [Frappe Helpdesk Docs](https://docs.frappe.io/helpdesk) — Project-specific docs
- [Vue 3 Style Guide](https://vuejs.org/style-guide/) — Vue.js best practices
- [Tailwind CSS](https://tailwindcss.com/docs) — Utility-first CSS framework

---

**For updates, merge new conventions here. If anything is unclear or missing, ask for clarification.**
