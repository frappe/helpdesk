<template>
  <Dialog v-model="show" :options="{ title: __('Change Email') }">
    <template #body-content>
      <div class="flex flex-col gap-2">
        <FormControl label="New Email" type="email" v-model="newEmail" />
        <div class="text-p-sm text-ink-gray-5">Current: {{ auth.user }}</div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end items-center">
        <Button
          variant="solid"
          :label="__('Update')"
          @click="updateEmail.submit()"
          :loading="updateEmail.loading"
          :disabled="!isDirty"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { createResource, Dialog, FormControl, toast } from "frappe-ui";
import { __ } from "@/translation";
import { useAuthStore } from "@/stores/auth";
import { computed, ref } from "vue";

const auth = useAuthStore();

const show = defineModel<boolean>();

const newEmail = ref("");

const updateEmail = createResource({
  url: "frappe.client.rename_doc",
  makeParams() {
    return {
      doctype: "User",
      old_name: auth?.user,
      new_name: newEmail.value,
    };
  },
  onSuccess: () => {
    toast.success(__("Email updated successfully"));
    location.pathname = "/login";
  },
});

const isDirty = computed(() => {
  return newEmail.value.trim() ? newEmail.value !== auth.user : false;
});
</script>
