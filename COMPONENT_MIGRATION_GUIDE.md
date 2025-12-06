# Component Migration Guide - Frappe UI to DaisyUI

Quick reference for developers working on the Helpdesk app.

## Import Pattern

### ✅ Use Local Components (from @/components/ui)

```javascript
import {
  Button,
  Avatar,
  Badge,
  Tooltip,
  Dialog,
  Dropdown,
  Popover,
  Breadcrumbs,
  ErrorMessage,
  LoadingIndicator,
  FormControl,
  Switch,
  // Utilities
  call,
  createResource,
  createListResource,
  createDocumentResource,
  getCachedResource,
  getCachedListResource,
  toast,
  FeatherIcon,
} from '@/components/ui';
```

### ⚠️ Still Use Frappe UI (not yet migrated)

```javascript
import {
  Autocomplete,
  Input,
  TextInput,
  TextEditor,
  Select,
  Tabs,
  TabList,
  TabPanel,
  Checkbox,
  Radio,
  FileUploader,
  DatePicker,
  DateTimePicker,
  NestedPopover,
  Link,
  ListFooter,
  usePageMeta,
} from 'frappe-ui';
```

## Component API Reference

### Button

```vue
<Button
  label="Click Me"
  variant="solid"      <!-- solid, outline, ghost, minimal, subtle, link -->
  theme="primary"      <!-- primary, secondary, neutral, accent, success, warning, error, info -->
  size="md"           <!-- xs, sm, md, lg -->
  icon="plus"         <!-- Feather icon name -->
  iconPosition="left" <!-- left, right -->
  :loading="false"
  :disabled="false"
  @click="handleClick"
>
  <template #prefix>
    <FeatherIcon name="plus" />
  </template>
  Optional slot content
  <template #suffix>
    <FeatherIcon name="chevron-down" />
  </template>
</Button>
```

### Avatar

```vue
<Avatar
  :image="userImage"
  :label="userName"
  size="md"          <!-- xs, sm, md, lg, xl -->
  shape="circle"     <!-- circle, square -->
/>
```

### Badge

```vue
<Badge
  :label="text"
  variant="solid"    <!-- solid, outline, subtle -->
  theme="primary"    <!-- primary, secondary, neutral, accent, success, warning, error, info -->
  size="md"          <!-- sm, md, lg -->
/>
```

### Dialog

```vue
<Dialog
  v-model="isOpen"
  :dismissable="true"
>
  <template #header>
    <h3>Dialog Title</h3>
  </template>
  <template #body>
    <p>Dialog content</p>
  </template>
  <template #footer>
    <Button @click="save">Save</Button>
  </template>
</Dialog>
```

### Dropdown

```vue
<Dropdown
  :options="menuOptions"
  label="Menu"
  placement="bottom"  <!-- top, bottom, left, right, bottom-end, etc. -->
  @select="handleSelect"
>
  <template #default>
    <Button>Custom Trigger</Button>
  </template>
</Dropdown>

<!-- Options format -->
const menuOptions = [
  { label: 'Edit', icon: 'edit', onClick: () => {} },
  { label: 'Delete', icon: 'trash', onClick: () => {} },
  { divider: true },
  { group: 'Section' },
  { label: 'Settings', icon: 'settings', shortcut: '⌘S' },
];
```

### Popover

```vue
<Popover placement="bottom">
  <template #target="{ togglePopover }">
    <Button @click="togglePopover">Show Popover</Button>
  </template>
  <template #content>
    <div class="p-4">Popover content</div>
  </template>
</Popover>
```

### Breadcrumbs

```vue
<Breadcrumbs :items="breadcrumbItems" @click="handleBreadcrumbClick" />

<!-- Items format -->
const breadcrumbItems = [
  { label: 'Home', route: '/', icon: 'home' },
  { label: 'Tickets', route: '/tickets' },
  { label: 'Current Ticket' },
];
```

### Tooltip

```vue
<Tooltip text="This is a tooltip" placement="top">
  <Button>Hover me</Button>
</Tooltip>
```

### ErrorMessage

```vue
<ErrorMessage
  message="An error occurred"
  variant="error"  <!-- error, warning, info, success -->
  icon="alert-circle"
/>
```

### FormControl

```vue
<FormControl
  label="Field Label"
  hint="Optional hint text"
  error="Error message"
  :required="true"
>
  <Input v-model="value" />
</FormControl>
```

### Switch

```vue
<Switch
  v-model="isEnabled"
  label="Enable feature"
  :disabled="false"
/>
```

### LoadingIndicator

```vue
<LoadingIndicator size="md" />  <!-- sm, md, lg -->
```

## Migration Examples

### Example 1: Simple Button Migration

```vue
<!-- Before -->
<template>
  <Button variant="solid" @click="save">Save</Button>
</template>

<script setup>
import { Button } from 'frappe-ui';
</script>

<!-- After -->
<template>
  <Button variant="solid" @click="save">Save</Button>
</template>

<script setup>
import { Button } from '@/components/ui';
</script>
```

### Example 2: Mixed Components

```vue
<!-- Before -->
<script setup>
import { Button, Avatar, Autocomplete } from 'frappe-ui';
</script>

<!-- After (split imports) -->
<script setup>
import { Button, Avatar } from '@/components/ui';
import { Autocomplete } from 'frappe-ui';
</script>
```

### Example 3: Resource Utilities

```vue
<!-- Before -->
<script setup>
import { createResource, call } from 'frappe-ui';
</script>

<!-- After -->
<script setup>
import { createResource, call } from '@/components/ui';
</script>
```

## Common Patterns

### Pattern 1: Form with Mixed Components

```vue
<template>
  <form @submit.prevent="handleSubmit">
    <FormControl label="Name" :required="true">
      <Input v-model="name" />  <!-- From frappe-ui -->
    </FormControl>

    <FormControl label="Category">
      <Autocomplete  <!-- From frappe-ui -->
        v-model="category"
        :options="categories"
      />
    </FormControl>

    <Switch v-model="isActive" label="Active" />  <!-- Local -->

    <div class="flex gap-2 mt-4">
      <Button variant="solid" type="submit">Save</Button>  <!-- Local -->
      <Button variant="ghost" @click="cancel">Cancel</Button>  <!-- Local -->
    </div>
  </form>
</template>

<script setup>
// Local components
import { Button, FormControl, Switch } from '@/components/ui';
// Frappe UI components (not yet migrated)
import { Input, Autocomplete } from 'frappe-ui';
</script>
```

### Pattern 2: List with Actions

```vue
<template>
  <div v-for="item in items" :key="item.id" class="flex items-center gap-2">
    <Avatar :image="item.image" :label="item.name" />  <!-- Local -->
    <div class="flex-1">
      <h3>{{ item.name }}</h3>
      <Badge :label="item.status" />  <!-- Local -->
    </div>
    <Dropdown :options="getActions(item)" @select="handleAction">  <!-- Local -->
      <Button icon="more-horizontal" variant="ghost" />  <!-- Local -->
    </Dropdown>
  </div>
</template>

<script setup>
import { Avatar, Badge, Button, Dropdown } from '@/components/ui';
</script>
```

### Pattern 3: Modal Dialog

```vue
<template>
  <Button @click="showDialog = true">Open Dialog</Button>  <!-- Local -->

  <Dialog v-model="showDialog">  <!-- Local -->
    <template #header>
      <h3>Edit Item</h3>
    </template>
    <template #body>
      <FormControl label="Name">  <!-- Local -->
        <Input v-model="name" />  <!-- Frappe UI -->
      </FormControl>
      <FormControl label="Description">  <!-- Local -->
        <TextEditor v-model="description" />  <!-- Frappe UI -->
      </FormControl>
    </template>
    <template #footer>
      <Button @click="save">Save</Button>  <!-- Local -->
      <Button variant="ghost" @click="showDialog = false">Cancel</Button>  <!-- Local -->
    </template>
  </Dialog>
</template>

<script setup>
import { Button, Dialog, FormControl } from '@/components/ui';
import { Input, TextEditor } from 'frappe-ui';
</script>
```

## Styling

### DaisyUI Classes

All local components use DaisyUI classes. You can customize them using DaisyUI's utility classes:

```vue
<Button class="btn-wide">Wide Button</Button>
<Button class="btn-block">Full Width</Button>
<Avatar class="ring ring-primary ring-offset-base-100 ring-offset-2" />
```

### Theme Colors

Available theme colors (use with `theme` prop):
- `primary` - Main brand color
- `secondary` - Secondary brand color
- `accent` - Accent color
- `neutral` - Neutral gray
- `success` - Green (success states)
- `warning` - Yellow/Orange (warnings)
- `error` - Red (errors)
- `info` - Blue (information)

### Sizes

Most components support these sizes:
- `xs` - Extra small
- `sm` - Small
- `md` - Medium (default)
- `lg` - Large
- `xl` - Extra large (where applicable)

## Tips

1. **Always split imports**: Keep local components separate from frappe-ui imports
2. **Check the index.js**: See `/desk/src/components/ui/index.js` for available components
3. **Use DaisyUI classes**: Customize with DaisyUI utility classes
4. **Maintain consistency**: Use the same patterns across the codebase
5. **Document new components**: If you create new local components, add them to this guide

## Support

If you need a component that's not yet migrated:
1. Use the frappe-ui version
2. Document the usage
3. Consider implementing the local version

---

Last Updated: 2025-12-04
