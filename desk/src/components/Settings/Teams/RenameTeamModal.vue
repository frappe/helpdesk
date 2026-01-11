<template>
  <Dialog v-model="dialog.show" :options="renameDialogOptions">
    <template #body-content>
      <FormControl
        v-model="teamName"
        :label="__('Title')"
        :placeholder="__('Product Experts')"
      />
    </template>
    <template #actions>
      <Button
        variant="solid"
        @click="renameTeam"
        :loading="renameTeamResource.loading"
        :disabled="teamName == dialog.teamName || teamName.trim() == ''"
      >
        {{ __("Confirm") }}
      </Button>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { createResource, Dialog, toast } from "frappe-ui";
import { computed, ref, watch } from "vue";

const emit = defineEmits(["onRename"]);

const dialog = defineModel<{
  show: boolean;
  teamName: string;
}>();
const teamName = ref(dialog.value.teamName);

const renameTeamResource = createResource({
  url: "frappe.client.rename_doc",
  makeParams() {
    return {
      doctype: "HD Team",
      old_name: dialog.value.teamName,
      new_name: teamName.value,
    };
  },
  validate(params) {
    if (!params.new_name) return __("New title is required");
    if (params.new_name === params.old_name)
      return __("New and old title cannot be same");
  },
  onSuccess(data) {
    toast.success(__("Team renamed"));
    dialog.value.show = false;
    emit("onRename", data);
  },
});

const renameDialogOptions = computed(() => ({
  title: __("Rename team"),
  message: __("Enter the new name for the team"),
}));

function renameTeam() {
  renameTeamResource.submit();
}

watch(
  () => dialog.value.show,
  () => {
    teamName.value = dialog.value.teamName;
  }
);
</script>
