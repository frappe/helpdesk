<template>
  <div class="flex items-center py-2">
    <div class="w-full">
      <div class="text-base">{{ data.name }}</div>
      <div
        class="text-sm text-gray-500 mt-1 whitespace-nowrap overflow-ellipsis overflow-hidden"
      >
        {{ data.description }}
      </div>
    </div>
    <div class="flex justify-between items-center">
      <div>
        <Dropdown
          :options="[
            {
              label: 'Edit',
              onClick: () => editHolidayList(),
              icon: 'edit',
            },
            {
              label: 'Duplicate',
              onClick: () => duplicate(),
              icon: 'copy',
            },
            {
              label: isConfirmingDelete ? 'Confirm Delete' : 'Delete',
              onClick: () => deleteHolidayList(),
              icon: 'trash-2',
            },
          ]"
        >
          <Button icon="more-horizontal" variant="ghost" />
        </Dropdown>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { Button, Dropdown, createResource } from "frappe-ui";
import { ref } from "vue";
import { activeScreen, holidayListData } from "./holidaylist";

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
});

const isConfirmingDelete = ref(false);

const duplicate = () => {
  createResource({
    url: "helpdesk.api.holiday_list.duplicate_holiday_list",
    params: {
      docname: props.data.name,
    },
    onSuccess: () => {
      holidayListData.reload();
    },
    auto: true,
  });
};

const editHolidayList = () => {
  activeScreen.value = {
    screen: "view",
    data: props.data,
  };
};

const deleteHolidayList = () => {
  event.preventDefault();
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
    setTimeout(() => {
      isConfirmingDelete.value = false;
    }, 3000);
    return;
  }

  createResource({
    url: "frappe.client.delete",
    params: {
      doctype: "HD Service Holiday List",
      name: props.data.name,
    },
    onSuccess: () => {
      holidayListData.reload();
      isConfirmingDelete.value = false;
    },
    auto: true,
  });
};
</script>
