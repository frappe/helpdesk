<template>
  <div>
    <header class="flex justify-between mb-4">
      <div>
        <h1 class="text-lg font-semibold mb-1">Field Dependencies</h1>
        <p class="text-ink-gray-6 text-base">
          Dynamically control field options based on selection
        </p>
      </div>
      <Button
        label="New"
        variant="solid"
        size="sm"
        @click="$emit('update:step', 'fd')"
      >
        <template #prefix>
          <LucidePlus class="h-4 w-4 stroke-1.5" />
        </template>
      </Button>
    </header>

    <div class="w-full">
      <!-- table heading -->
      <div class="flex w-full p-2 border-b">
        <p class="w-7/12 text-p-sm text-ink-gray-5">Name</p>
        <p class="w-3/12 text-p-sm text-ink-gray-5">Created By</p>
        <p class="w-1/12 text-p-sm text-ink-gray-5">Enabled</p>
        <p class="w-1/12 text-p-sm text-ink-gray-5"></p>
      </div>

      <!-- Table content -->
      <div v-if="!list.loading && list.data?.length > 0">
        <!-- Each row -->
        <div
          class="w-full flex flex-col items-center cursor-pointer group hover:rounded border-b transition hover:bg-surface-gray-2"
          v-for="(row, idx) in list.data"
          @click.stop="$emit('update:step', 'fd', row.name)"
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
              <Switch v-model="row.enabled" @click.stop />
            </p>
            <!-- More Options -->
            <p class="w-1/12 flex items-center justify-end">
              <Dropdown placement="right" :options="options">
                <Button variant="ghost">
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
            v-if="idx < list.data?.length - 1"
          /> -->
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { createListResource, Avatar, Switch } from "frappe-ui";
import { getFieldDependencyLabel } from "@/utils";

const list = createListResource({
  doctype: "HD Form Script",
  filters: { is_standard: 1, name: ["like", "%Field Dependency%"] },
  fields: ["name", "enabled", "owner"],
  auto: true,
  cache: ["FD", "List"],
});

const options = [
  {
    label: "Delete",
    icon: "trash",
  },
];
</script>
