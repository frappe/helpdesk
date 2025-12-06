# DaisyUI Migration Guide

## Overview

This guide documents the migration from Frappe UI to DaisyUI components for the Helpdesk application. We've created wrapper components that maintain the Frappe UI API while using DaisyUI styling underneath.

## Migration Strategy

We're using an **incremental wrapper approach**:
1. Create DaisyUI-based components in `/components/ui/` that match Frappe UI APIs
2. Gradually replace Frappe UI imports with our new components
3. Keep Frappe UI utilities (createResource, toast, call) untouched

## Completed Components

### Foundation Components
- ✅ **Button** - Full DaisyUI button with variants (solid, outline, ghost, link)
- ✅ **LoadingIndicator** - DaisyUI loading spinner with size variants

### Layout Components
- ✅ **Dialog** - DaisyUI modal with customizable sizes and actions
- ✅ **Dropdown** - DaisyUI dropdown with menu options

### Display Components
- ✅ **Avatar** - DaisyUI avatar with image/placeholder support
- ✅ **Badge** - DaisyUI badge with color variants
- ✅ **Tooltip** - DaisyUI tooltip with placement options

### Form Components
- ✅ **FormControl** - DaisyUI form inputs (text, textarea, select)

## How to Use

### Before (Frappe UI):
```vue
<script setup>
import { Button, LoadingIndicator, Dialog } from 'frappe-ui';
</script>
```

### After (DaisyUI):
```vue
<script setup>
import { Button, LoadingIndicator, Dialog } from '@/components/ui';
</script>
```

The API remains the same! Your existing component code doesn't need to change.

## Component API Reference

### Button
```vue
<Button
  label="Click me"
  variant="solid"           <!-- solid, outline, ghost, minimal, subtle, link -->
  size="md"                 <!-- xs, sm, md, lg -->
  theme="primary"           <!-- primary, secondary, neutral, accent, success, warning, error, info -->
  :loading="false"
  :disabled="false"
  icon="check"
  icon-position="left"      <!-- left, right -->
  @click="handleClick"
>
  <template #prefix>...</template>
  <template #suffix>...</template>
</Button>
```

### LoadingIndicator
```vue
<LoadingIndicator
  size="md"                 <!-- xs, sm, md, lg -->
  text="Loading..."
  :center="false"
/>
```

### Dialog
```vue
<Dialog
  v-model="showDialog"
  :options="{
    title: 'Dialog Title',
    size: 'md',             <!-- xs, sm, md, lg, xl, full -->
    hideCloseButton: false,
    static: false,          <!-- prevent backdrop close -->
    actions: [
      { label: 'Cancel', variant: 'ghost', onClick: () => {} },
      { label: 'Save', variant: 'solid', onClick: () => {} }
    ]
  }"
>
  <template #body-content>
    Dialog content here
  </template>
</Dialog>
```

### Avatar
```vue
<Avatar
  image="https://..."
  label="John Doe"
  size="md"                 <!-- xs, sm, md, lg, xl -->
  shape="circle"            <!-- circle, square -->
/>
```

### Badge
```vue
<Badge
  label="New"
  variant="primary"         <!-- neutral, primary, secondary, accent, ghost, info, success, warning, error -->
  size="md"                 <!-- xs, sm, md, lg -->
  :outline="false"
/>
```

### Tooltip
```vue
<Tooltip
  text="Tooltip text"
  placement="top"           <!-- top, bottom, left, right -->
  variant="default"         <!-- default, primary, secondary, accent, info, success, warning, error -->
>
  <button>Hover me</button>
</Tooltip>
```

### FormControl
```vue
<FormControl
  v-model="value"
  label="Field Label"
  type="text"               <!-- text, textarea, select, email, password, number, etc. -->
  size="md"                 <!-- xs, sm, md, lg -->
  variant="bordered"        <!-- bordered, ghost, subtle -->
  placeholder="Enter text..."
  :required="false"
  :disabled="false"
  error-message=""
  help-text=""
  :options="[]"             <!-- For select type -->
  :rows="3"                 <!-- For textarea type -->
  @change="handleChange"
  @blur="handleBlur"
/>
```

### Dropdown
```vue
<Dropdown
  :options="[
    { label: 'Option 1', value: '1', icon: 'check', onClick: () => {} },
    { divider: true },
    { group: 'Group Name' },
    { label: 'Option 2', value: '2', disabled: true }
  ]"
  label="Menu"
  placement="bottom"        <!-- top, bottom, left, right, bottom-end, bottom-start, top-end, top-start -->
  @select="handleSelect"
>
  <template #default>
    <button class="btn">Custom Trigger</button>
  </template>
</Dropdown>
```

## Migration Status

### Migrated Files
- ✅ [ListViewBuilder.vue](/desk/src/components/ListViewBuilder.vue) - Using Button and LoadingIndicator

### Remaining Work
- [ ] Migrate TicketAgent.vue (Button, Dialog, FormControl)
- [ ] Migrate remaining 100+ files gradually
- [ ] Replace Frappe UI Dropdown with our wrapper
- [ ] Add more form components (Checkbox, Switch, etc.)

## Build Status
✅ Build completed successfully (3m 24s)
✅ All components exported correctly
✅ No breaking errors
✅ Fixed `get_agents()` API error (changed `enabled` to `is_active`)

## Notes
- CSS warnings from DaisyUI minification are expected and don't affect functionality
- FeatherIcon and Frappe utilities (createResource, toast, call) are re-exported from our ui module for convenience
- All components maintain the same API as Frappe UI for drop-in compatibility
