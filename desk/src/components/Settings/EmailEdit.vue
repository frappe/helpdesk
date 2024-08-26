<template>
  <div class="flex h-full flex-col gap-4">
    <!-- title and desc -->
    <div role="heading" aria-level="1" class="flex flex-col gap-1">
      <h5 class="text-lg font-semibold">Edit Email</h5>
    </div>
    <div class="w-fit">
      <EmailProviderIcon
        :logo="emailIcon[accountData.service]"
        :service-name="accountData.service"
      />
    </div>
    <div class="flex flex-col gap-2">
      <div class="grid grid-cols-1 gap-4">
        <div
          v-for="field in fields"
          :key="field.name"
          class="flex flex-col gap-1"
        >
          <FormControl
            v-model="state[field.name]"
            :label="field.label"
            :name="field.name"
            :type="field.type"
            :placeholder="field.placeholder"
          />
        </div>
      </div>
      <ErrorMessage v-if="error" class="ml-1" message="error" />
    </div>
    <div class="mt-auto flex justify-between">
      <Button
        label="Back"
        theme="gray"
        variant="outline"
        @click="emit('update:step', 'email-list')"
      />
      <Button
        label="Update Account"
        variant="solid"
        @click="console.log('Update')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import EmailProviderIcon from "./EmailProviderIcon.vue";
import {
  emailIcon,
  services,
  popularProviderFields,
  customProviderFields,
} from "./emailConfig";
import { EmailAccountResource } from "@/types";

interface Props {
  accountData: EmailAccountResource;
}

const props = withDefaults(defineProps<Props>(), {
  accountData: null,
});

const emit = defineEmits(["update:step"]);

const state = reactive({
  email_account_name: props.accountData.name || "",
  email_id: props.accountData.email_id || "",
  password: props.accountData?.password || "",
  api_key: props.accountData?.api_key || "",
  api_secret: props.accountData?.api_secret || "",
});
const error = ref("");

const fields = computed(() => {
  const service = services.find((s) => s.name === props.accountData.service);
  if (service.custom) {
    return customProviderFields;
  }
  return popularProviderFields;
});
</script>

<style scoped></style>
