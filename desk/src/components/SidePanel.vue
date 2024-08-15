<template>
  <div class="sidebarContainer flex w-full flex-col divide-y">
    <!-- section 1 -->
    <div class="bg-white px-4 py-2.5">
      <div class="flex flex-1 items-center justify-between">
        <span class="text-lg font-semibold">Help</span>
        <Button
          theme="gray"
          variant="ghost"
          icon="x"
          @click="() => console.log('Close Sidebar')"
        />
      </div>
    </div>
    <!-- section 2 -->
    <div class="flex-1">
      <!-- heading and button -->
      <div class="flex items-center justify-between px-4 py-2.5">
        <span class="text-lg font-semibold">Popular Topics</span>
        <Button
          theme="gray"
          variant="ghost"
          label="View All"
          @click="openDocumentation"
        />
      </div>
      <!-- list of articles -->
      <div />
    </div>
    <!-- section 3 -->
    <div class="flex-1 px-4 py-2.5">
      <div class="flex items-center justify-between">
        <span class="text-lg font-semibold">Get Started</span>
        <Badge
          label="60% Progress"
          theme="green"
          variant="subtle"
          class="p-0.5"
        />
      </div>
      <!-- list of articles -->
      <div />
    </div>
  </div>
</template>

<script setup lang="ts">
function openDocumentation() {
  const URL = "https://docs.frappe.io/helpdesk";
  window.open(URL, "_blank");
}
</script>

<style scoped>
.sidebarContainer {
  position: fixed;
  top: 12px;
  bottom: 12px;
  right: 12px;
  background-color: rgb(251, 251, 251);
  box-shadow: rgba(28, 40, 64, 0.12) 0px 8px 28px -6px,
    rgba(28, 40, 64, 0.14) 0px 18px 88px -4px;
  border-radius: 12px;
  overflow: auto;
  width: 360px;
  z-index: 9999;
  animation: fadeinright 200ms ease-in-out forwards;
}

.unmount {
  animation: fadeinright 200ms ease-in-out forwards;
}

@keyframes fadeinright {
  from {
    opacity: 0;
    transform: translateX(12px);
  }
  to {
    opacity: 1;
    transform: translateX(0px);
  }
}
@keyframes fadeinleft {
  from {
    opacity: 1;
    transform: translateX(0px);
  }
  to {
    opacity: 0;
    transform: translateX(12px);
  }
}
</style>
