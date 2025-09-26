<template>
  <SettingsHeader :routes="routes" />
  <div class="max-w-3xl xl:max-w-4xl mx-auto w-full p-4 lg:py-8">
    <div>
      <SettingsLayoutHeader>
        <template #title>
          <div class="flex items-center gap-2">
            <h1 class="text-xl font-semibold text-ink-gray-8">
              Field Dependencies
            </h1>
            <DocumentationButton
              url="https://docs.frappe.io/helpdesk/field-dependency"
              color="!text-ink-gray-6"
            />
          </div>
        </template>
        <template #description>
          <p class="text-p-base text-ink-gray-6 mt-1">
            Create dependencies between fields to dynamically control options
            based on user selections.
          </p>
        </template>
        <template #actions>
          <Button
            label="New"
            theme="gray"
            variant="solid"
            @click="router.push({ name: 'NewFieldDependency' })"
            icon-left="plus"
          />
        </template>
      </SettingsLayoutHeader>
    </div>
    <div class="pb-8">
      <!-- Loading State -->
      <div
        v-if="fieldDependenciesList.loading"
        class="flex items-center justify-center py-4 mt-11"
      >
        <LoadingIndicator :scale="5" />
      </div>

      <!-- Empty State -->
      <div
        v-if="
          !fieldDependenciesList.loading &&
          fieldDependenciesList.data?.length === 0
        "
        class="flex flex-col items-center justify-center gap-3 rounded-md border border-gray-200 p-4 mt-7 h-[500px]"
      >
        <div class="text-lg font-medium text-ink-gray-4">
          {{ __("No Field Dependencies found.") }}
        </div>
        <Button
          label="New"
          variant="subtle"
          icon-left="plus"
          @click="router.push({ name: 'NewFieldDependency' })"
        />
      </div>

      <div
        class="w-full mt-4"
        v-if="
          !fieldDependenciesList.loading &&
          fieldDependenciesList.data?.length > 0
        "
      >
        <!-- table heading -->
        <div class="grid grid-cols-8 sm:grid-cols-11 items-center p-2">
          <p class="col-span-3 sm:col-span-7 text-p-sm text-ink-gray-5">Name</p>
          <p class="col-span-3 sm:col-span-2 text-p-sm text-ink-gray-5">
            Created By
          </p>
          <p class="col-span-2 text-p-sm text-ink-gray-5">Enabled</p>
        </div>
        <div class="h-px border-t mx-1 border-outline-gray-modals" />

        <!-- Table content -->
        <ul>
          <!-- Each row -->
          <li
            class="w-full flex flex-col items-center cursor-pointer hover:bg-surface-menu-bar rounded"
            v-for="(row, idx) in fieldDependenciesList.data"
            @click.stop="
              router.push({
                name: 'EditFieldDependency',
                params: { id: row.name },
              })
            "
            :key="row.name"
          >
            <div
              class="w-full grid grid-cols-8 sm:grid-cols-11 items-center p-2"
            >
              <!-- Parent to Child -->
              <div
                class="col-span-3 sm:col-span-7 text-base text-ink-gray-7 pr-3"
              >
                <span>{{ getFieldDependencyLabel(row.name) }}</span>
              </div>
              <!-- Owner -->
              <p class="col-span-3 sm:col-span-2 flex items-center gap-2 pr-3">
                <Avatar size="sm" :image="row.owner" :label="row.owner" />
                <span class="text-base text-ink-gray-7 truncate">{{
                  row.owner
                }}</span>
              </p>
              <!-- Enabled -->
              <p class="col-span-2 flex items-center justify-between">
                <Switch
                  :model-value="row.enabled"
                  @update:modelValue="(e) => handleSwitchToggle(row.name, e)"
                  @click.stop
                />
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
  </div>
</template>

<script setup lang="ts">
import SettingsHeader from "../components/SettingsHeader.vue";
import SettingsLayoutHeader from "@/pages/settings/components/SettingsLayoutHeader.vue";
import { Avatar, Button, LoadingIndicator, Switch, toast } from "frappe-ui";
import { getFieldDependencyLabel, ConfirmDelete } from "@/utils";
import { computed, onMounted, ref } from "vue";
import DocumentationButton from "@/components/DocumentationButton.vue";
import { fieldDependenciesList } from "./fieldDependency";
import { useRouter } from "vue-router";

const router = useRouter();
const routes = computed(() => [
  {
    label: "Field Dependencies",
    route: "/settings/field-dependencies",
  },
]);

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
