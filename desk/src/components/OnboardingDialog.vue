<template>
  <Dialog
    v-model="showOnboardingDialog"
    :options="{
      title: 'Help',
      size: 'xl',
    }"
  >
    <template #body-content>
      <!-- section 2 -->
      <div class="flex-1 px-4 py-2.5">
        <!-- heading and button -->
        <div class="flex items-center justify-between">
          <span class="text-lg font-semibold">Popular Topics</span>
          <Button
            theme="gray"
            variant="subtle"
            label="View All"
            icon-right="arrow-up-right"
            @click="openDocumentation"
          />
        </div>
        <!-- list of articles -->
        <div>
          <p v-for="i in 4" :key="i">Article {{ i }}</p>
        </div>
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
        <div>
          <p v-for="i in 4" :key="i">Step {{ i }}</p>
        </div>
        <div />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
const showOnboardingDialog = defineModel();
function openDocumentation() {
  const URL = "https://docs.frappe.io/helpdesk";
  window.open(URL, "_blank");
}
</script>

<style scoped></style>
