// DaisyUI-based components
// These components provide a clean, modern UI using DaisyUI styling

// Foundation Components
export { default as Button } from './Button.vue';
export { default as LoadingIndicator } from './LoadingIndicator.vue';

// Layout Components
export { default as Dialog } from './Dialog.vue';
export { default as Dropdown } from './Dropdown.vue';
export { default as Popover } from './Popover.vue';
export { default as Breadcrumbs } from './Breadcrumbs.vue';

// Display Components
export { default as Avatar } from './Avatar.vue';
export { default as Badge } from './Badge.vue';
export { default as Tooltip } from './Tooltip.vue';
export { default as ErrorMessage } from './ErrorMessage.vue';

// Form Components
export { default as FormControl } from './FormControl.vue';
export { default as Switch } from './Switch.vue';

// Re-export Frappe UI utilities that we're keeping
export {
  call,
  createResource,
  createListResource,
  createDocumentResource,
  getCachedResource,
  getCachedListResource,
  toast,
  FeatherIcon,
} from 'frappe-ui';
