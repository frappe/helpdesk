# Skeleton

Generic loading placeholder with no per-component configuration. Structured
like a frappe-ui component (`Skeleton.vue`, `types.ts`, `index.ts`) so it can
be lifted upstream as-is.

## Bone mode

Without a default slot it renders a single gray pulse block, shaped by props
or utility classes:

```vue
<Skeleton class="h-4 w-40" />
<Skeleton variant="circle" width="2rem" height="2rem" />
<Skeleton variant="box" height="8rem" />
```

## Mask mode

With a default slot and `loading` true, the slot renders inert (`aria-hidden`,
no pointer events) and every leaf node — text, images, icons, buttons,
inputs — is masked into a gray pulse block matching its real size. Once
`loading` is false the slot renders untouched, so it wraps real content:

```vue
<Skeleton :loading="ticket.loading">
  <TicketCard :ticket="ticket.data ?? mockTicket" />
</Skeleton>
```

Mask mode only needs the component to *render its structure*; pass mock props
when data is still loading. Components that fetch their own data should not be
masked (they would fire real requests) — compose bones instead.
