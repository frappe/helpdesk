<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex items-center gap-2">
        <h1 class="text-lg-semibold text-ink-gray-8">
          {{ __("Field Dependencies") }}
        </h1>
      </div>
    </template>
    <template #description>
      <p class="text-p-sm max-w-md text-ink-gray-6">
        {{
          __(
            "Create field dependencies to dynamically update options based on user selections. Learn more about field dependencies"
          )
        }}
        <a
          href="https://docs.frappe.io/helpdesk/field-dependency"
          target="_blank"
          class="underline"
          >{{ __("here.") }}</a
        >
      </p>
    </template>
    <template #header-actions>
      <Button
        :label="__('New')"
        theme="gray"
        variant="solid"
        @click="$emit('update:step', 'fd')"
        icon-left="lucide-plus"
        class="rtl:flex-row-reverse"
      />
    </template>
    <template #content>
      <div class="grow">
        <!-- Loading State -->
        <div
          v-if="fieldDependenciesList.loading"
          class="flex items-center justify-center py-4"
        >
          <LoadingIndicator :scale="5" />
        </div>

        <!-- Empty State -->
        <EmptyState
          v-if="
            !fieldDependenciesList.loading &&
            !fieldDependenciesList.data?.length
          "
          variant="badge"
          :icon="FieldDependencyIcon"
          title="No field dependency found"
          description="Add one to get started."
        />

        <div
          class="w-full -ms-2"
          v-if="
            !fieldDependenciesList.loading &&
            fieldDependenciesList.data?.length > 0
          "
        >
          <div>
            <div
              class="grid grid-cols-11 items-center gap-4 text-sm text-ink-gray-5"
            >
              <div class="col-span-7 ms-2">{{ __("Name") }}</div>
              <div class="col-span-2">{{ __("Created by") }}</div>
              <div class="col-span-2">{{ __("Enabled") }}</div>
            </div>
            <hr class="mt-2 mx-2" />
            <div
              v-for="(row, index) in fieldDependenciesList.data"
              :key="row.name"
            >
              <div
                class="grid grid-cols-11 items-center gap-4 cursor-pointer hover:bg-surface-sidebar rounded h-12.5"
              >
                <div
                  @click.stop="$emit('update:step', 'fd', row.name)"
                  class="w-full py-3 ps-2 col-span-7 text-base text-ink-gray-7"
                >
                  <span>{{ getFieldDependencyLabel(row.name) }}</span>
                </div>
                <div class="col-span-2 flex items-center gap-1">
                  <Avatar size="sm" :image="row.owner" :label="row.owner" />
                  <span class="text-base text-ink-gray-7 truncate">{{
                    row.owner
                  }}</span>
                </div>
                <div
                  class="flex justify-between items-center w-full pe-2 col-span-2"
                >
                  <div>
                    <Switch
                      :model-value="Boolean(row.enabled)"
                      @update:modelValue="(e) => handleSwitchToggle(row, e)"
                      @click.stop
                    />
                  </div>
                  <div>
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
                  </div>
                </div>
              </div>
              <hr
                v-if="index !== fieldDependenciesList.data.length - 1"
                class="mx-2"
              />
            </div>
          </div>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import {
  Avatar,
  Button,
  Dropdown,
  LoadingIndicator,
  Switch,
  toast,
} from "frappe-ui";
import { getFieldDependencyLabel, ConfirmDelete } from "@/utils";
import { onMounted, ref } from "vue";
import { fieldDependenciesList } from "./fieldDependency";
import FieldDependencyIcon from "@/components/icons/FieldDependencyIcon.vue";
import { __ } from "@/translation";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";

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
          toast.success(__("Field dependency deleted successfully."));
          fieldDependenciesList.reload();
        },
      });
    },
  });
}

function handleSwitchToggle(row: any, value: boolean) {
  // Optimistically reflect the new state so the controlled Switch stays in
  // sync; without this the bound value never changes and toggling keeps
  // re-sending the same value (the disable never takes effect).
  row.enabled = value;
  fieldDependenciesList.setValue.submit(
    {
      name: row.name,
      enabled: value,
    },
    {
      onSuccess: () => {
        toast.success(__("Field dependency updated successfully."));
      },
      onError: () => {
        row.enabled = !value;
        toast.error(__("Failed to update field dependency."));
      },
    }
  );
}
</script>
