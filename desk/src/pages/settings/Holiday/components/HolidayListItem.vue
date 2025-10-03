<template>
  <div class="flex items-center cursor-pointer relative group rounded my-1">
    <div
      class="w-full flex flex-col justify-center h-12.5"
      @click="
        router.push({
          name: 'EditBusinessHolidays',
          params: { id: data.name },
        })
      "
    >
      <div
        class="text-base text-ink-gray-7 font-medium overflow-ellipsis overflow-hidden"
      >
        {{ data.name }}
      </div>
      <div
        v-if="data.description && data.description.length > 0"
        class="text-sm text-ink-gray-5 mt-1 whitespace-nowrap overflow-ellipsis overflow-hidden"
      >
        {{ data.description }}
      </div>
    </div>
    <div class="flex justify-between items-center pr-2">
      <div>
        <Dropdown :options="dropdownOptions">
          <Button
            icon="more-horizontal"
            variant="ghost"
            @click="isConfirmingDelete = false"
          />
        </Dropdown>
      </div>
    </div>
    <div
      class="absolute -left-2.5 -top-1 w-full h-full group-hover:bg-gray-50 rounded-md z-[-1]"
      :style="{
        width: 'calc(100% + 20px)',
        height: 'calc(100% + 8px)',
      }"
    />
  </div>
  <Dialog
    :options="{ title: `Duplicate Holiday List` }"
    v-model="duplicateDialog.show"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          label="New Holiday List Name"
          type="text"
          v-model="duplicateDialog.name"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex gap-2 justify-end">
        <Button
          variant="subtle"
          label="Close"
          @click="duplicateDialog.show = false"
        />
        <Button variant="solid" label="Duplicate" @click="duplicate()" />
      </div>
    </template>
  </Dialog>
</template>
<script setup lang="ts">
import { Button, createResource, toast } from "frappe-ui";
import { inject, ref } from "vue";
import { ConfirmDelete } from "@/utils";
import { useRouter } from "vue-router";

const router = useRouter();

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
});

const holidayList = inject<any>("holidayList");

const duplicateDialog = ref({
  show: false,
  name: "",
});

const isConfirmingDelete = ref(false);

const dropdownOptions = [
  {
    label: "Duplicate",
    onClick: () => {
      duplicateDialog.value.show = true;
      duplicateDialog.value.name = props.data.name + " (Copy)";
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
    url: "helpdesk.api.holiday_list.duplicate_holiday_list",
    params: {
      docname: props.data.name,
      new_name: duplicateDialog.value.name,
    },
    onSuccess: (data) => {
      holidayList.reload();
      toast.success("Holiday list duplicated");
      duplicateDialog.value = {
        show: false,
        name: "",
      };
      router.push({
        name: "EditBusinessHolidays",
        params: { id: data.name },
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

  holidayList.delete.submit(props.data.name, {
    onSuccess: () => {
      toast.success("Holiday list deleted");
    },
  });
};
</script>
