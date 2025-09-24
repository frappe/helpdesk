<template>
  <div>
    <SettingsHeader :routes="routes" />
    <div class="w-full max-w-3xl xl:max-w-4xl mx-auto p-4 lg:py-8">
      <SettingsLayoutHeader title="SLA Policies">
        <template #description>
          <p class="text-p-base max-w-md text-ink-gray-6 mt-1">
            SLAs align your team and customers with defined timelines for a
            reliable experience.
            <a
              href="https://docs.frappe.io/helpdesk/service-level-agreement"
              target="_blank"
              class="underline"
              >Learn more about SLA
            </a>
          </p>
        </template>
        <template #actions>
          <Button
            label="New"
            theme="gray"
            variant="solid"
            @click="goToNew()"
            icon-left="plus"
          />
        </template>
      </SettingsLayoutHeader>
      <div
        v-if="slaPolicyList.list.loading && !slaPolicyList.list.data"
        class="flex items-center justify-center mt-12"
      >
        <LoadingIndicator class="w-4" />
      </div>
      <div v-else>
        <div
          v-if="slaPolicyList.list.data?.length === 0"
          class="flex items-center justify-center rounded-md border border-gray-200 p-4 mt-7"
        >
          <div class="text-sm text-ink-gray-7">No SLA Policies found</div>
        </div>
        <div v-else>
          <div
            class="grid grid-cols-8 sm:grid-cols-6 items-center gap-3 text-sm text-gray-600 ml-2 mt-6"
          >
            <div class="col-span-6 sm:col-span-5 text-p-sm">Policy Name</div>
            <div class="col-span-2 sm:col-span-1 text-p-sm">Enabled</div>
          </div>
          <hr class="mt-2 mx-2" />
          <div v-for="sla in slaPolicyList.list.data" :key="sla.name">
            <SlaPolicyListItem :data="sla" />
            <hr class="mx-2" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { createListResource, LoadingIndicator } from "frappe-ui";
import SettingsHeader from "../components/SettingsHeader.vue";
import { useRouter } from "vue-router";
import { computed, provide } from "vue";
import SlaPolicyListItem from "./components/SlaPolicyListItem.vue";
import SettingsLayoutHeader from "@/pages/settings/components/SettingsLayoutHeader.vue";

const router = useRouter();

const slaPolicyList = createListResource({
  doctype: "HD Service Level Agreement",
  fields: ["name", "default_sla", "enabled", "description"],
  orderBy: "creation desc",
  start: 0,
  pageLength: 999,
  auto: true,
});

provide("slaPolicyList", slaPolicyList);

const routes = computed(() => [
  {
    label: "SLA Policies",
    route: "/settings/sla-policies",
  },
]);

const goToNew = () => {
  router.push({ name: "NewSLAPolicy" });
};
</script>
