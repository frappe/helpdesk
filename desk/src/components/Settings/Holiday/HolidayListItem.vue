<template>
  <div class="flex items-center cursor-pointer hover:bg-gray-50 rounded">
    <div
      class="w-full pl-2 flex flex-col justify-center h-14"
      @click="holidayListActiveScreen = { screen: 'view', data: data }"
    >
      <div class="text-base text-ink-gray-7 font-medium">{{ data.name }}</div>
      <div
        v-if="data.description && data.description.length > 0"
        class="text-sm text-ink-gray-5 mt-1 truncate"
      >
        {{ data.description }}
      </div>
    </div>
    <div class="flex justify-between items-center pr-2">
      <div>
        <Dropdown placement="right" :options="dropdownOptions">
          <Button
            icon="more-horizontal"
            variant="ghost"
            @click="isConfirmingDelete = false"
          />
        </Dropdown>
      </div>
    </div>
  </div>
  <Dialog
    :options="{ title: __('Duplicate Holiday List') }"
    v-model="duplicateDialog.show"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          :label="__('New Holiday List Name')"
          type="text"
          v-model="duplicateDialog.newName"
          maxlength="100"
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
import {
  Button,
  Dialog,
  createResource,
  Dropdown,
  FormControl,
  toast,
} from "frappe-ui";
import { inject, ref } from "vue";
import { holidayListActiveScreen } from "@/stores/holidayList";
import { ConfirmDelete } from "@/utils";
import { __ } from "@/translation";
import { HolidayListResourceSymbol } from "@/types";
import { HDServiceHolidayList } from "@/types/doctypes";

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
});

const holidayList = inject(HolidayListResourceSymbol);

const duplicateDialog = ref({
  show: false,
  newName: "",
  name: "",
});

const isConfirmingDelete = ref(false);

const dropdownOptions = [
  {
    label: __("Duplicate"),
    onClick: () => {
      duplicateDialog.value = {
        show: true,
        newName: props.data.name + " (Copy)",
        name: props.data.name,
      };
    },
    icon: "copy",
  },
  ...ConfirmDelete({
    onConfirmDelete: () => deleteHolidayList(),
    isConfirmingDelete,
  }),
];

const duplicate = () => {
  createResource({
    url: "frappe.client.get",
    params: {
      doctype: "HD Service Holiday List",
      name: duplicateDialog.value.name,
    },
    onSuccess: (data: HDServiceHolidayList) => {
      createResource({
        url: "frappe.client.insert",
        params: {
          doc: {
            ...data,
            holiday_list_name: duplicateDialog.value.newName,
            name: duplicateDialog.value.newName,
          },
        },
        auto: true,
        onSuccess(newHolidayListData: HDServiceHolidayList) {
          holidayList?.reload();
          toast.success(__("Holiday list duplicated"));
          duplicateDialog.value = {
            show: false,
            newName: "",
            name: "",
          };
          setTimeout(() => {
            holidayListActiveScreen.value = {
              screen: "view",
              data: newHolidayListData,
            };
          }, 250);
        },
      });
    },
    auto: true,
  });
};

const deleteHolidayList = () => {
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
    return;
  }

  holidayList?.delete.submit(props.data.name, {
    onSuccess: () => {
      toast.success(__("Holiday list deleted"));
    },
  });
};
</script>
