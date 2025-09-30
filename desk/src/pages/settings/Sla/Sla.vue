<template>
  <div>
    <SettingsHeader :routes="routes" />
    <div
      class="max-w-3xl xl:max-w-4xl mx-auto w-full px-4 relative flex flex-col-reverse pb-6"
    >
      <div
        v-if="slaPolicyList.list.loading && !slaPolicyList.list.data"
        class="flex items-center justify-center mt-12"
      >
        <LoadingIndicator class="w-4" />
      </div>
      <div v-else>
        <div
          v-if="!slaPolicyList.list.loading && !slaPolicyList.list.data?.length"
          class="flex flex-col items-center justify-center gap-4 p-4 h-[500px]"
        >
          <div class="p-4 size-16 rounded-full bg-surface-gray-1">
            <ShieldCheck class="size-8 text-ink-gray-6" />
          </div>
          <div class="flex flex-col items-center gap-1">
            <div class="text-lg font-medium text-ink-gray-6">No SLA found</div>
            <div class="text-base text-ink-gray-5 max-w-60 text-center">
              No SLA available. Add your first SLA to get started.
            </div>
          </div>
          <Button
            label="Add SLA"
            variant="outline"
            icon-left="plus"
            @click="goToNew()"
          />
        </div>
        <div v-else>
          <div
            class="grid grid-cols-8 sm:grid-cols-6 items-center gap-3 text-sm text-gray-600 ml-2"
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
      <div class="bg-white py-4 lg:py-8 lg:pb-6 sticky top-0">
        <SettingsLayoutHeader title="SLA Policies">
          <template #description>
            <p class="text-p-base text-ink-gray-6 mt-1">
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
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button, createListResource, LoadingIndicator } from "frappe-ui";
import SettingsHeader from "../components/SettingsHeader.vue";
import { useRouter } from "vue-router";
import { computed, provide } from "vue";
import SlaPolicyListItem from "./components/SlaPolicyListItem.vue";
import SettingsLayoutHeader from "@/pages/settings/components/SettingsLayoutHeader.vue";
import ShieldCheck from "~icons/lucide/shield-check";
import { resetSlaData } from "@/stores/sla";

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
  resetSlaData();
  router.push({ name: "NewSLAPolicy" });
};
</script>
