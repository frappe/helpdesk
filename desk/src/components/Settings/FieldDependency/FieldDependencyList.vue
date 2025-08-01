<template>
  <div class="px-10 py-8">
    <SettingsLayoutHeader>
      <template #title>
        <h1 class="text-lg font-semibold text-ink-gray-8">
          Field Dependencies
        </h1>
      </template>
      <template #description>
        <p class="text-sm max-w-md leading-5 text-ink-gray-6">
          Create dependencies between fields to dynamically control options
          based on user selections.
        </p>
      </template>
      <template #actions>
        <Button
          label="New"
          theme="gray"
          variant="solid"
          @click="$emit('update:step', 'fd')"
          icon-left="plus"
        />
      </template>
    </SettingsLayoutHeader>
  </div>
  <div class="px-10 pb-8">
    <!-- Loading State -->
    <div
      v-if="fieldDependenciesList.loading"
      class="flex items-center justify-center py-4"
    >
      <LoadingIndicator :scale="5" />
    </div>

    <!-- Empty State -->
    <div
      v-if="
        !fieldDependenciesList.loading &&
        fieldDependenciesList.data?.length === 0
      "
      class="flex mt-28 justify-between w-full h-full"
    >
      <p class="text-sm text-gray-500 w-full flex justify-center">
        No field dependencies found.
      </p>
    </div>

    <div
      class="w-full"
      v-if="
        !fieldDependenciesList.loading && fieldDependenciesList.data?.length > 0
      "
    >
      <!-- table heading -->
      <div class="flex w-full p-2 border-b">
        <p class="w-7/12 text-p-sm text-ink-gray-5">Name</p>
        <p class="w-3/12 text-p-sm text-ink-gray-5">Created By</p>
        <p class="w-1/12 text-p-sm text-ink-gray-5">Enabled</p>
        <p class="w-1/12 text-p-sm text-ink-gray-5"></p>
      </div>

      <!-- Table content -->
      <div>
        <!-- Each row -->
        <div
          class="w-full flex flex-col items-center cursor-pointer group hover:rounded border-b transition hover:bg-surface-gray-2"
          v-for="row in fieldDependenciesList.data"
          @click.stop="$emit('update:step', 'fd', row.name)"
          :key="row.name"
        >
          <div class="w-full flex items-center p-2">
            <!-- Parent to Child -->
            <div class="flex gap-2 w-7/12 text-base text-ink-gray-7 pr-3">
              <span>{{ getFieldDependencyLabel(row.name) }}</span>
            </div>
            <!-- Owner -->
            <p class="w-3/12 flex items-center gap-2 pr-3">
              <Avatar size="sm" :image="row.owner" :label="row.owner" />
              <span class="text-base text-ink-gray-7 truncate">{{
                row.owner
              }}</span>
            </p>
            <!-- Enabled -->
            <p class="w-1/12 flex items-center">
              <Switch
                :model-value="row.enabled"
                @update:modelValue="(e) => handleSwitchToggle(row.name, e)"
                @click.stop
              />
            </p>
            <!-- More Options -->
            <p class="w-1/12 flex items-center justify-end">
              <Dropdown placement="right" :options="options">
                <Button variant="ghost" @click.stop>
                  <template #icon>
                    <LucideMoreHorizontal class="h-4 w-4" />
                  </template>
                </Button>
              </Dropdown>
            </p>
          </div>
          <!-- Separator -->
          <!-- <div
              class="mx-3 h-px border-t border-outline-gray-modals transition-opacity group-hover:opacity-0 w-full"
              v-if="idx < fieldDependenciesList.data?.length - 1"
            /> -->
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Avatar, LoadingIndicator, Switch } from "frappe-ui";
import { getFieldDependencyLabel } from "@/utils";
import { onMounted } from "vue";
import { fieldDependenciesList } from "./fieldDependency";
import SettingsLayoutHeader from "../SettingsLayoutHeader.vue";

onMounted(() => {
  fieldDependenciesList.reload();
});

const options = [
  {
    label: "Delete",
    icon: "trash",
  },
];

function handleSwitchToggle(rowName: string, value: boolean) {
  fieldDependenciesList.setValue.submit(
    {
      name: rowName,
      enabled: value,
    },
    {
      onSuccess: () => {
        fieldDependenciesList.reload();
      },
    }
  );
}
</script>
