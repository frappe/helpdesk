<template>
  <!-- Margin keeps the 32px hit area but takes one title line, so headers match. -->
  <Button
    variant="ghost"
    icon-left="lucide-chevron-left"
    size="md"
    class="my-[calc((1lh-2rem)/2)] [&_*]:!leading-[inherit] cursor-pointer -ms-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 text-ink-gray-7 !text-lg !font-semibold hover:opacity-70 !pe-0 !max-w-96 !shrink min-w-0 !justify-start rtl:flex-row-reverse rtl:ps-4"
  />
</template>

<script setup lang="ts">
import { Button } from "frappe-ui";
</script>
