<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex items-center gap-2">
        <h1 class="text-lg font-semibold text-ink-gray-8">
          {{ __("Field Dependencies") }}
        </h1>
        <DocumentationButton
          url="https://docs.frappe.io/helpdesk/field-dependency"
          color="!text-ink-gray-6"
        />
      </div>
    </template>
    <template #description>
      <p class="text-p-sm max-w-md text-ink-gray-6">
        {{
          __(
            "Create dependencies between fields to dynamically control options based on user selections."
          )
        }}
      </p>
    </template>
    <template #header-actions>
      <Button
        :label="__('New')"
        theme="gray"
        variant="solid"
        @click="$emit('update:step', 'fd')"
        icon-left="plus"
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
        <div
          v-if="
            !fieldDependenciesList.loading &&
            !fieldDependenciesList.data?.length
          "
          class="flex flex-col items-center justify-center gap-4 p-4 h-full"
        >
          <div
            class="p-4 size-14.5 rounded-full bg-surface-gray-1 flex justify-center items-center"
          >
            <FieldDependencyIcon class="size-6 text-ink-gray-6" />
          </div>
          <div class="flex flex-col items-center gap-1">
            <div class="text-base font-medium text-ink-gray-6">
              {{ __("No field dependency found") }}
            </div>
            <div class="text-p-sm text-ink-gray-5 max-w-60 text-center">
              {{ __("Add your first field dependency to get started") }}
            </div>
          </div>
          <Button
            :label="__('New')"
            variant="outline"
            icon-left="plus"
            @click="$emit('update:step', 'fd')"
          />
        </div>

        <div
          class="w-full -ml-2"
          v-if="
            !fieldDependenciesList.loading &&
            fieldDependenciesList.data?.length > 0
          "
        >
          <div>
            <div
              class="grid grid-cols-11 items-center gap-4 text-sm text-gray-600"
            >
              <div class="col-span-7 ml-2">{{ __("Name") }}</div>
              <div class="col-span-2">{{ __("Created By") }}</div>
              <div class="col-span-2">{{ __("Enabled") }}</div>
            </div>
            <hr class="mt-2 mx-2" />
            <div
              v-for="(row, index) in fieldDependenciesList.data"
              :key="row.name"
            >
              <div
                class="grid grid-cols-11 items-center gap-4 cursor-pointer hover:bg-gray-50 rounded h-12.5"
              >
                <div
                  @click.stop="$emit('update:step', 'fd', row.name)"
                  class="w-full py-3 pl-2 col-span-7 text-base text-ink-gray-7"
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
                  class="flex justify-between items-center w-full pr-2 col-span-2"
                >
                  <div>
                    <Switch
                      :model-value="row.enabled"
                      @update:modelValue="
                        (e) => handleSwitchToggle(row.name, e)
                      "
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
import { Avatar, Button, LoadingIndicator, Switch, toast } from "frappe-ui";
import { getFieldDependencyLabel, ConfirmDelete } from "@/utils";
import { onMounted, ref } from "vue";
import { fieldDependenciesList } from "./fieldDependency";
import DocumentationButton from "@/components/DocumentationButton.vue";
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
          toast.success(__("Field dependency deleted successfully"));
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
        toast.success(__("Field dependency updated successfully."));
      },
    }
  );
}
</script>
