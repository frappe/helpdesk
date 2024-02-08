<template>
  <header class="flex h-12 items-center justify-between border-b py-2.5 pl-5">
    <div class="flex items-center gap-2">
      <slot name="left-header" />
    </div>
    <div class="flex items-center gap-2 px-5">
      <slot name="right-header" class="flex items-center gap-2" />
    </div>
  </header>
</template>
