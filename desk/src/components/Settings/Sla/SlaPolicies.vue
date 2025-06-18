<template>
  <div>
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-lg font-semibold">Service Level Agreements (SLAs)</h1>
        <p class="text-sm text-gray-700 mt-2 max-w-md">
          SLAs align your team and customers with defined timelines for a
          reliable experience.
          <a
            href="https://docs.frappe.io/helpdesk/service-level-agreement"
            target="_blank"
            class="text-gray-700 underline"
            >Learn more about SLA
          </a>
        </p>
      </div>
      <Button
        label="Create new"
        theme="gray"
        variant="solid"
        @click="goToNew()"
      >
        <template #prefix>
          <LucidePlus class="h-4 w-4" />
        </template>
      </Button>
    </div>
    <div class="mt-6">
      <SlaPolicyList />
    </div>
  </div>
</template>

<script setup lang="ts">
import { slaPolicyListData, activeScreen } from "./sla";
import SlaPolicyList from "./SlaPolicyList.vue";
import { onMounted } from "vue";

onMounted(() => {
  slaPolicyListData.fetch();
});

const goToNew = () => {
  activeScreen.value = {
    screen: "view",
    data: null,
  };
};
</script>
