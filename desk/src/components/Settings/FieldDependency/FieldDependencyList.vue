<template>
  <div class="px-10 py-8">
    <SettingsLayoutHeader>
      <template #title>
        <div class="flex items-center gap-2">
          <h1 class="text-lg font-semibold text-ink-gray-8">
            Field Dependencies
          </h1>
          <DocumentationButton
            url="https://docs.frappe.io/helpdesk/field-dependency"
            color="!text-ink-gray-6"
          />
        </div>
      </template>
      <template #description>
        <p class="text-p-sm max-w-md text-ink-gray-6">
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
      <div class="flex w-full p-2">
        <p class="w-7/12 text-p-sm text-ink-gray-5">Name</p>
        <p class="w-3/12 text-p-sm text-ink-gray-5">Created By</p>
        <p class="w-1/12 text-p-sm text-ink-gray-5">Enabled</p>
        <p class="w-1/12 text-p-sm text-ink-gray-5"></p>
      </div>
      <div class="h-px border-t mx-1 border-outline-gray-modals" />

      <!-- Table content -->
      <ul>
        <!-- Each row -->
        <li
          class="w-full flex flex-col items-center cursor-pointer hover:bg-surface-menu-bar rounded"
          v-for="(row, idx) in fieldDependenciesList.data"
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
              <Dropdown placement="right" :options="getOptions(row.name)">
                <Button
                  variant="ghost"
                  @click.stop="
                    () => {
                      isConfirmingDelete = false;
                    }
                  "
                >
                  <template #icon>
                    <LucideMoreHorizontal class="h-4 w-4" />
                  </template>
                </Button>
              </Dropdown>
            </p>
          </div>
          <!-- Separator -->
          <div
            class="h-px border-b mx-1 border-outline-gray-modals w-[99%]"
            v-if="idx < fieldDependenciesList.data?.length - 1"
          />
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Avatar, LoadingIndicator, Switch, toast } from "frappe-ui";
import { getFieldDependencyLabel, ConfirmDelete } from "@/utils";
import { onMounted, ref } from "vue";
import { fieldDependenciesList } from "./fieldDependency";
import SettingsLayoutHeader from "../SettingsLayoutHeader.vue";
import DocumentationButton from "@/components/DocumentationButton.vue";

onMounted(() => {
  fieldDependenciesList.reload();
});

const isConfirmingDelete = ref(false);

function getOptions(rowName: string) {
  return ConfirmDelete({
    isConfirmingDelete,
    onConfirmDelete: () => {
      fieldDependenciesList.delete.submit(rowName, {
        onSuccess: () => {
          toast.success("Field dependency deleted successfully");
          fieldDependenciesList.reload();
        },
      });
    },
  });
}

function handleSwitchToggle(rowName: string, value: boolean) {
  fieldDependenciesList.setValue.submit(
    {
      name: rowName,
      enabled: value,
    },
    {
      onSuccess: () => {
        toast.success("Field dependency updated successfully.");
      },
    }
  );
}
</script>
