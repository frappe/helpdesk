<template>
  <div
    class="grid grid-cols-8 sm:grid-cols-6 items-center gap-4 cursor-pointer hover:bg-gray-50 rounded"
  >
    <div
      @click="router.push({ name: 'EditSLAPolicy', params: { id: data.name } })"
      class="w-full py-3 pl-2 col-span-6 sm:col-span-5"
    >
      <div
        class="text-base text-ink-gray-7 font-medium flex items-center gap-2"
      >
        {{ data.name }}
        <Badge v-if="data.default_sla" color="gray" size="sm">Default</Badge>
      </div>
      <div
        v-if="data.description && data.description.length > 0"
        class="text-sm w-full text-ink-gray-5 mt-1 whitespace-nowrap overflow-ellipsis overflow-hidden"
      >
        {{ data.description }}
      </div>
    </div>
    <div
      class="flex justify-between items-center w-full sm:pr-2 col-span-2 sm:col-span-1"
    >
      <div>
        <Switch
          size="sm"
          :modelValue="data.enabled"
          @update:modelValue="onToggle"
        />
      </div>
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
  </div>
  <Dialog
    :options="{ title: `Duplicate SLA Policy` }"
    v-model="duplicateDialog.show"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          label="New SLA Policy Name"
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
import {
  Switch,
  Button,
  createResource,
  toast,
  Dialog,
  Badge,
} from "frappe-ui";
import { ref, inject } from "vue";
import { ConfirmDelete } from "@/utils";
import { useRouter } from "vue-router";

const slaPolicyList = inject<any>("slaPolicyList");
const router = useRouter();

const duplicateDialog = ref({
  show: false,
  name: "",
});

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
});

const isConfirmingDelete = ref(false);

const dropdownOptions = [
  {
    label: "Duplicate",
    onClick: () => {
      duplicateDialog.value = {
        show: true,
        name: props.data.name + " (Copy)",
      };
    },
    icon: "copy",
  },
  ...ConfirmDelete({
    onConfirmDelete: () => deleteSla(),
    isConfirmingDelete,
  }),
];

const duplicate = () => {
  createResource({
    url: "helpdesk.api.sla.duplicate_sla",
    params: {
      docname: props.data.name,
      new_name: duplicateDialog.value.name,
    },
    onSuccess: (data) => {
      slaPolicyList.reload();
      toast.success("SLA policy duplicated");
      duplicateDialog.value = {
        show: false,
        name: "",
      };
      router.push({ name: "EditSLAPolicy", params: { id: data.name } });
    },
    auto: true,
  });
};

const deleteSla = () => {
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
    return;
  }

  slaPolicyList.delete.submit(props.data.name, {
    onSuccess: () => {
      toast.success("SLA policy deleted");
    },
  });
};

const onToggle = () => {
  if (props.data.default_sla) {
    toast.error("SLA set as default cannot be disabled");
    return;
  }
  slaPolicyList.setValue.submit(
    {
      name: props.data.name,
      enabled: !props.data.enabled,
    },
    {
      onSuccess: () => {
        toast.success("SLA policy status updated");
      },
    }
  );
};
</script>
