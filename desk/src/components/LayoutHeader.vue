<template>
  <header class="container flex justify-between items-center px-5 py-2.5 h-12">
      <div class="">
      <slot name="left-header" />
    </div>
    <div class="">
      <slot name="right-header" class="" />
    </div>
  </header>
</template>
  