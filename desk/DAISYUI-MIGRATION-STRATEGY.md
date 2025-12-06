# DaisyUI Migration Strategy

## DaisyUI Architecture & Best Practices

### Core Principles

1. **DaisyUI is CSS-only** - No JavaScript, uses Tailwind classes
2. **Native HTML elements** - Uses semantic HTML with utility classes
3. **Component classes** - Use DaisyUI's semantic classes (btn, modal, dropdown)
4. **Theme-based** - Centralized theming through tailwind.config.js
5. **No runtime dependencies** - Pure CSS, lighter bundle

### DaisyUI vs HeadlessUI

| Feature | HeadlessUI | DaisyUI |
|---------|------------|---------|
| Type | JavaScript components | CSS-only classes |
| Bundle Size | ~50kb | ~8kb CSS |
| Accessibility | Built-in ARIA | Manual ARIA on HTML |
| Customization | Props + styling | Tailwind classes |
| Complexity | Higher | Lower |

## Migration Approach: Two Options

### Option A: Continue Forward (Recommended)
**Pros:**
- 274 files already migrated successfully
- Build is working
- Most components converted
- Less disruption

**Cons:**
- Still have HeadlessUI remnants
- Mixed architecture temporarily

**Strategy:**
1. Keep current DaisyUI components
2. Replace remaining 9 HeadlessUI files
3. Remove HeadlessUI dependency when done

### Option B: Revert & Restart
**Pros:**
- Clean slate
- More methodical approach
- Better documentation during process

**Cons:**
- Lose 274 file migrations
- Significant rework
- More time required

## Recommended: Option A - Phased Completion

### Phase 1: Low-Risk Replacements (Start Here)
**Replace simple components first:**

1. **Dialogs/Modals**
   - HeadlessUI: `<Dialog>`
   - DaisyUI: `<dialog>` with `.modal` class
   ```vue
   <!-- Before: HeadlessUI -->
   <Dialog :open="isOpen">...</Dialog>

   <!-- After: DaisyUI -->
   <dialog class="modal" :class="{ 'modal-open': isOpen }">
     <div class="modal-box">...</div>
   </dialog>
   ```

2. **Dropdowns/Menus**
   - HeadlessUI: `<Menu>`, `<MenuButton>`, `<MenuItems>`
   - DaisyUI: `<details>` with `.dropdown` class
   ```vue
   <!-- Before: HeadlessUI -->
   <Menu>
     <MenuButton>Open</MenuButton>
     <MenuItems>...</MenuItems>
   </Menu>

   <!-- After: DaisyUI -->
   <details class="dropdown">
     <summary class="btn">Open</summary>
     <ul class="menu dropdown-content">...</ul>
   </details>
   ```

### Phase 2: Form Components
**Replace Combobox, Autocomplete, MultiSelect**

DaisyUI doesn't have these built-in, so you have 3 options:

1. **Use native HTML + DaisyUI styling**
   ```vue
   <select class="select select-bordered" multiple>
     <option>Option 1</option>
   </select>
   ```

2. **Build custom with DaisyUI primitives**
   ```vue
   <div class="dropdown">
     <input class="input input-bordered" />
     <ul class="menu dropdown-content">
       <!-- Custom logic here -->
     </ul>
   </div>
   ```

3. **Keep HeadlessUI for complex forms** (Pragmatic choice)
   - Autocomplete is complex to rebuild
   - HeadlessUI excels at accessible form controls
   - Can coexist with DaisyUI

### Phase 3: Complex Interactive Components
**Command Palette, Mobile Sidebar**

These are complex - consider:
1. Use DaisyUI drawer for sidebar
2. Build command palette with DaisyUI modal + custom logic
3. Or keep HeadlessUI for these (pragmatic)

## File-by-File Migration Plan

### Immediate (Easy Wins)

1. ✅ **MobileSidebar.vue** → DaisyUI `.drawer`
2. ✅ **NestedPopover.vue** → DaisyUI `.dropdown` or `.popover`

### Moderate Effort

3. ⚠️ **Autocomplete.vue** → Custom DaisyUI or keep HeadlessUI
4. ⚠️ **MultiSelectInput.vue** → Custom DaisyUI or keep HeadlessUI
5. ⚠️ **AssigneeSearch.vue** → Reuse new Autocomplete approach

### Keep HeadlessUI (Pragmatic)

6. 🔄 **CP.vue** (Command Palette) - Complex, keep HeadlessUI
7. 🔄 **frappe-ui/** components - External library, leave alone

## Tailwind + DaisyUI Best Practices

### 1. Use Semantic DaisyUI Classes
```vue
<!-- Good: DaisyUI semantic classes -->
<button class="btn btn-primary">Click</button>

<!-- Avoid: Only Tailwind utilities -->
<button class="px-4 py-2 bg-blue-500 text-white rounded">Click</button>
```

### 2. Theme Configuration
```js
// tailwind.config.js
daisyui: {
  themes: [
    {
      light: {
        "primary": "#570df8",
        "secondary": "#f000b8",
        "accent": "#1dcdbc",
        "neutral": "#2b3440",
        "base-100": "#ffffff",
      },
    },
  ],
  base: false,  // ← We disabled this to prevent conflicts
}
```

### 3. Component Structure
```vue
<template>
  <!-- DaisyUI class for structure -->
  <div class="card bg-base-100 shadow-xl">
    <!-- Tailwind for adjustments -->
    <div class="card-body p-4 sm:p-6">
      <!-- DaisyUI for interactive elements -->
      <button class="btn btn-primary">
        <!-- Tailwind for fine-tuning -->
        <span class="text-sm">Click</span>
      </button>
    </div>
  </div>
</template>
```

### 4. Responsive Design
```vue
<!-- DaisyUI + Tailwind responsive -->
<div class="btn btn-sm md:btn-md lg:btn-lg">
  Responsive Button
</div>
```

## Decision Matrix

| Keep HeadlessUI If: | Migrate to DaisyUI If: |
|---------------------|------------------------|
| Complex form controls | Simple UI components |
| Needs heavy JS logic | CSS-only sufficient |
| Accessibility critical | Can add ARIA manually |
| Combobox/Autocomplete | Button/Modal/Dropdown |
| Rich interactions | Static display |

## Recommended Action Plan

### Immediate Next Steps:

1. **Keep current progress** - Don't revert
2. **Replace MobileSidebar** with DaisyUI drawer (easy win)
3. **Assess form components** - Decide keep vs rebuild
4. **Remove unused HeadlessUI** after replacements
5. **Document which components use what**

### Success Criteria:

- ✅ All simple components use DaisyUI
- ✅ Complex forms: Pragmatic choice made
- ✅ No unused dependencies
- ✅ Consistent styling across app
- ✅ Build size reduced
- ✅ Maintainable architecture

## Resources

- **DaisyUI Docs**: https://daisyui.com/components/
- **DaisyUI GitHub**: https://github.com/saadeghi/daisyui
- **Tailwind Docs**: https://tailwindcss.com/docs
- **Accessibility**: https://www.w3.org/WAI/ARIA/

## Migration Checklist

- [x] Create DaisyUI base components
- [x] Migrate 274 simple component imports
- [x] Fix Tailwind config conflicts
- [ ] Replace MobileSidebar with DaisyUI drawer
- [ ] Replace NestedPopover with DaisyUI dropdown
- [ ] Decision: Autocomplete (keep or rebuild?)
- [ ] Decision: MultiSelectInput (keep or rebuild?)
- [ ] Decision: Command Palette (keep or rebuild?)
- [ ] Remove HeadlessUI dependency (if fully migrated)
- [ ] Update documentation
- [ ] Final testing
