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
      <template
        v-if="
          fieldDependenciesList.data?.length > 0 ||
          fieldDependencySearchQuery.length
        "
        #bottom-section
      >
        <div class="relative">
          <Input
            v-model="fieldDependencySearchQuery"
            @input="fieldDependencySearchQuery = $event"
            placeholder="Search"
            type="text"
            class="bg-white hover:bg-white focus:ring-0 border-outline-gray-2"
            icon-left="search"
            debounce="300"
            inputClass="p-4 pr-12"
          />
          <Button
            v-if="fieldDependencySearchQuery"
            icon="x"
            variant="ghost"
            @click="fieldDependencySearchQuery = ''"
            class="absolute right-1 top-1/2 -translate-y-1/2"
          />
        </div>
      </template>
    </SettingsLayoutHeader>
  </div>
  <div class="px-10 pb-8 overflow-y-auto">
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
        !fieldDependenciesList.loading && !fieldDependenciesList.data?.length
      "
      class="flex flex-col items-center justify-center gap-4 p-4 mt-7 h-[500px]"
    >
      <div class="p-4 size-16 rounded-full bg-surface-gray-1">
        <FieldDependencyIcon class="size-8 text-ink-gray-6" />
      </div>
      <div class="flex flex-col items-center gap-1">
        <div class="text-lg font-medium text-ink-gray-6">
          No field dependency found
        </div>
        <div class="text-base text-ink-gray-5 max-w-60 text-center">
          Add your first field dependency to get started.
        </div>
      </div>
      <Button
        label="New"
        variant="outline"
        icon-left="plus"
        @click="$emit('update:step', 'fd')"
      />
    </div>

    <div
      class="w-full -ml-2"
      v-if="
        !fieldDependenciesList.loading && fieldDependenciesList.data?.length > 0
      "
    >
      <div>
        <div class="grid grid-cols-11 items-center gap-4 text-sm text-gray-600">
          <div class="col-span-7 ml-2">{{ __("Name") }}</div>
          <div class="col-span-2">{{ __("Created By") }}</div>
          <div class="col-span-2">{{ __("Enabled") }}</div>
        </div>
        <hr class="mt-2 mx-2" />
        <div v-for="row in fieldDependenciesList.data" :key="row.name">
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
                  @update:modelValue="(e) => handleSwitchToggle(row.name, e)"
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
          <hr class="mx-2" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Avatar, LoadingIndicator, Switch, toast } from "frappe-ui";
import { getFieldDependencyLabel, ConfirmDelete } from "@/utils";
import { inject, onMounted, Ref, ref, watch } from "vue";
import { fieldDependenciesList } from "./fieldDependency";
import SettingsLayoutHeader from "../SettingsLayoutHeader.vue";
import DocumentationButton from "@/components/DocumentationButton.vue";
import FieldDependencyIcon from "@/components/icons/FieldDependencyIcon.vue";

onMounted(() => {
  fieldDependenciesList.reload();
});

const fieldDependencySearchQuery = inject<Ref>("fieldDependencySearchQuery");

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

watch(fieldDependencySearchQuery, (newValue) => {
  fieldDependenciesList.filters = {
    name: ["like", `%${newValue}%`],
  };
  if (!newValue) {
    fieldDependenciesList.start = 0;
    fieldDependenciesList.pageLength = 10;
  }
  fieldDependenciesList.reload();
});
</script>
