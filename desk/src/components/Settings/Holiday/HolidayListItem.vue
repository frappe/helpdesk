<template>
  <div class="flex items-center cursor-pointer hover:bg-gray-50 rounded">
    <div
      class="w-full py-3 pl-2"
      @click="holidayListActiveScreen = { screen: 'view', data: data }"
    >
      <div class="text-base">{{ data.name }}</div>
      <div
        v-if="data.description && data.description.length > 0"
        class="text-sm text-gray-500 mt-1 whitespace-nowrap overflow-ellipsis overflow-hidden"
      >
        {{ data.description }}
      </div>
    </div>
    <div class="flex justify-between items-center pr-2">
      <div>
        <Dropdown
          placement="right"
          :options="[
            {
              label: 'Duplicate',
              onClick: () => duplicate(),
              icon: 'copy',
            },
            {
              label: 'Confirm Delete',
              component: (props) =>
                TemplateOption({
                  option: isConfirmingDelete ? 'Confirm Delete' : 'Delete',
                  icon: 'trash-2',
                  active: props.active,
                  variant: isConfirmingDelete ? 'danger' : 'gray',
                  onClick: (event) => deleteHolidayList(event),
                }),
            },
          ]"
        >
          <Button
            icon="more-horizontal"
            variant="ghost"
            @click="isConfirmingDelete = false"
          />
        </Dropdown>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { Button, Dropdown, createResource, toast } from "frappe-ui";
import { ref } from "vue";
import { holidayListActiveScreen, holidayListData } from "./holidayList";
import { TemplateOption } from "@/utils";

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

const deleteHolidayList = (event) => {
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
    onError: (error) => {
      toast.error(error.messages[0]);
    },
    auto: true,
  });
};
</script>
