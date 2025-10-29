<template>
  <SettingsLayoutBase
    :title="__('Canned Responses')"
    :description="
      __(
        'Manage pre-defined responses that can be used to respond to customer queries.'
      )
    "
  >
    <template #actions>
      <Button
        label="New"
        theme="gray"
        variant="solid"
        @click="goToNew()"
        icon-left="plus"
      />
    </template>
    <template
      #bottom-section
      v-if="
        cannedResponseListData.data?.length > 9 ||
        cannedResponseSearchQuery.length
      "
    >
      <div class="relative">
        <Input
          v-model="cannedResponseSearchQuery"
          @input="cannedResponseSearchQuery = $event"
          :placeholder="__('Search')"
          type="text"
          class="bg-white hover:bg-white focus:ring-0 border-outline-gray-2"
          icon-left="search"
          debounce="300"
          inputClass="p-4 pr-12"
        />
        <Button
          v-if="cannedResponseSearchQuery"
          icon="x"
          variant="ghost"
          @click="cannedResponseSearchQuery = ''"
          class="absolute right-1 top-1/2 -translate-y-1/2"
        />
      </div>
    </template>
    <template #content>
      <div
        v-if="cannedResponseListData.loading && !cannedResponseListData.data"
        class="flex items-center justify-center mt-12"
      >
        <LoadingIndicator class="w-4" />
      </div>
      <div
        v-if="
          !cannedResponseListData.list.loading &&
          !cannedResponseListData.list.data?.length
        "
        class="flex flex-col items-center justify-center gap-4 p-4 h-[300px]"
      >
        <div
          class="p-4 size-14.5 rounded-full bg-surface-gray-1 flex justify-center items-center"
        >
          <LucideCloudLightning class="size-6 text-ink-gray-6" />
        </div>
        <div class="flex flex-col items-center gap-1">
          <div class="text-base font-medium text-ink-gray-6">
            {{ __("No Canned Response found") }}
          </div>
          <div class="text-p-sm text-ink-gray-5 max-w-60 text-center">
            {{ __("Add your first Canned response to get started.") }}
          </div>
        </div>
        <Button
          :label="__('Add Canned Response')"
          variant="outline"
          icon-left="plus"
          @click="goToNew()"
        />
      </div>
      <div v-else class="-ml-2">
        <div
          class="grid grid-cols-12 items-center gap-3 text-sm text-gray-600 ml-2"
        >
          <div class="col-span-9">{{ __("Name") }}</div>
          <div class="col-span-3">{{ __("Scope") }}</div>
        </div>
        <hr class="mt-2 mx-2" />
        <div
          v-for="(cannedResponse, index) in cannedResponseListData.data"
          :key="cannedResponse.name"
        >
          <div
            class="grid grid-cols-12 items-center gap-4 cursor-pointer hover:bg-gray-50 rounded"
          >
            <div
              @click="
                cannedResponseActiveScreen = {
                  screen: 'view',
                  data: cannedResponse,
                }
              "
              class="w-full px-2 flex flex-col justify-center h-12.5 col-span-9"
            >
              <div
                class="text-base text-ink-gray-7 font-medium w-full truncate"
              >
                {{ cannedResponse.name }}
              </div>
            </div>
            <div
              class="flex justify-between items-center w-full pr-2 col-span-3"
            >
              <div class="text-sm text-ink-gray-7">
                {{ cannedResponse.scope }}
              </div>
              <Dropdown
                placement="right"
                :options="dropdownOptions(cannedResponse)"
              >
                <Button
                  icon="more-horizontal"
                  variant="ghost"
                  @click="isConfirmingDelete = false"
                  class="mr-2"
                />
              </Dropdown>
            </div>
          </div>
          <hr
            v-if="index !== cannedResponseListData.data.length - 1"
            class="mx-2"
          />
        </div>
        <div class="flex justify-center">
          <Button
            v-if="
              !cannedResponseListData.loading &&
              cannedResponseListData.hasNextPage
            "
            class="mt-3.5 p-2"
            @click="() => cannedResponseListData.next()"
            :loading="cannedResponseListData.loading"
            label="Load More"
            icon-left="refresh-cw"
          />
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
  <Dialog
    :options="{ title: __('Duplicate Canned Response') }"
    v-model="duplicateDialog.show"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          :label="__('New Canned Response Name')"
          type="text"
          v-model="duplicateDialog.newName"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex gap-2 justify-end">
        <Button
          variant="subtle"
          :label="__('Close')"
          @click="duplicateDialog.show = false"
        />
        <Button variant="solid" :label="__('Duplicate')" @click="duplicate()" />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { Button, call, Input, toast } from "frappe-ui";
import SettingsLayoutBase from "../SettingsLayoutBase.vue";
import { inject, ref, Ref, watch } from "vue";
import { __ } from "@/translation";
import { ConfirmDelete } from "@/utils";
import LucideCloudLightning from "~icons/lucide/cloud-lightning";

const cannedResponseSearchQuery = inject<Ref>("cannedResponseSearchQuery");
const cannedResponseListData = inject<any>("cannedResponseListData");
const cannedResponseActiveScreen = inject<any>("cannedResponseActiveScreen");
const duplicateDialog = ref({
  show: false,
  name: "",
  newName: "",
});

const goToNew = () => {
  cannedResponseActiveScreen.value = {
    screen: "view",
    data: null,
  };
};

const isConfirmingDelete = ref(false);

const dropdownOptions = (cannedResponse) => [
  {
    label: __("Duplicate"),
    onClick: () => {
      duplicateDialog.value = {
        show: true,
        name: cannedResponse.name,
        newName: `${cannedResponse.name} (Copy)`,
      };
    },
    icon: "copy",
  },
  ...ConfirmDelete({
    onConfirmDelete: () => deleteCannedResponse(cannedResponse),
    isConfirmingDelete,
  }),
];

const deleteCannedResponse = (cannedResponse) => {
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
    return;
  }

  cannedResponseListData.delete.submit(cannedResponse.name, {
    onSuccess: () => {
      toast.success(__("Canned response deleted"));
    },
  });
};

const duplicate = async () => {
  await call("frappe.client.get", {
    doctype: "Email Template",
    name: duplicateDialog.value.name,
  }).then((data) => {
    cannedResponseListData.insert.submit(
      {
        ...data,
        name: duplicateDialog.value.newName,
      },
      {
        onSuccess: (data) => {
          toast.success(__("Canned response duplicated"));
          duplicateDialog.value = {
            show: false,
            name: "",
            newName: "",
          };
          cannedResponseActiveScreen.value = {
            screen: "view",
            data: { name: data.name },
          };
        },
      }
    );
  });
};

watch(cannedResponseSearchQuery, (newValue) => {
  cannedResponseListData.filters = {
    ...cannedResponseListData.filters,
    name: ["like", `%${newValue}%`],
  };
  if (!newValue) {
    cannedResponseListData.start = 0;
    cannedResponseListData.pageLength = 10;
  }
  cannedResponseListData.reload();
});
</script>
