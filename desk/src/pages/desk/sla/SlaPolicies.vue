<template>
  <div class="flex flex-col px-4">
    <ListManager
      ref="policyList"
      :options="{
        cache: ['SLA', 'Settings'],
        doctype: 'HD Service Level Agreement',
        urlQueryFilters: true,
        saveFiltersLocally: true,
        fields: ['name', 'default_sla', 'enabled'],
        limit: 20,
      }"
    >
      <template #body="{ manager }">
        <ListViewer
          :options="{
            name: 'Policy',
            base: '12',
            listTitle: 'Support Policies',
            filterBox: true,
            presetFilters: true,
            fields: {
              name: {
                label: 'Policy Name',
                width: 8,
              },
              enabled: {
                label: 'Active',
                width: 2,
              },
            },
          }"
          class="h-[calc(100vh-9.5rem)] pt-4 text-base"
          @add-item="
            () => {
              $router.push('/sla/new');
            }
          "
        >
          <template #field-name="{ row }">
            <div class="group flex w-full items-center">
              <RouterLink
                :to="{
                  path: `/sla/${row.name}`,
                }"
                class="font-inter flex flex-row items-center space-x-2 truncate pr-10 text-base text-gray-600 hover:text-gray-900 sm:w-10/12"
                ><div>
                  {{ `${row.name}` }}
                </div>
                <a title="Default service level agreement">
                  <CustomIcons
                    v-if="row.default_sla"
                    name="circle-check"
                    class="h-[16px] w-[16px] fill-blue-500"
                  />
                </a>
              </RouterLink>
            </div>
          </template>
          <template #field-enabled="{ row }">
            <div class="sm:w-2/12">
              <div class="flex flex-row-reverse">
                <CustomSwitch
                  v-model="row.enabled"
                  :disabled="row.default_sla"
                />
              </div></div
          ></template>
        </ListViewer>
      </template>
    </ListManager>
  </div>
</template>
<script>
import { inject } from "vue";
import ListManager from "@/components/global/ListManager.vue";
import ListViewer from "@/components/global/ListViewer.vue";
import CustomIcons from "@/components/desk/global/CustomIcons.vue";
import CustomSwitch from "@/components/global/CustomSwitch.vue";

export default {
  name: "SlaPolicies",
  components: {
    ListManager,
    ListViewer,
    CustomIcons,
    CustomSwitch,
  },
  setup() {
    const viewportWidth = inject("viewportWidth");

    return {
      viewportWidth,
    };
  },
  mounted() {
    this.$event.emit("set-selected-setting", "Support Policies");
  },
};
</script>
