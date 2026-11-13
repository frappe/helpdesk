<template>
  <Dialog
    v-model:open="show"
    :title="__('Set Phone Number')"
    :actions="[
      {
        label: __('Set Phone Number'),
        variant: 'solid',
        onClick: onSubmit,
      },
    ]"
  >
    <template #default>
      <div>
        <div class="text-base text-ink-gray-6">
          {{
            __("{0} does not have a phone number, set one to call them.", [
              contactDetails.name,
            ])
          }}
        </div>
        <div class="flex flex-col gap-2 mt-6">
          <PhoneControl
            v-model="contactDetails.phone"
            :label="__('Phone')"
            size="sm"
            variant="subtle"
            :disabled="false"
          />
          <ErrorMessage :message="error" />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { createResource, Dialog, ErrorMessage, toast } from "frappe-ui";
import { ref, watch } from "vue";
import { z } from "zod";
import { __ } from "@/translation";
import PhoneControl from "../frappe-ui/PhoneControl/PhoneControl.vue";

const emit = defineEmits(["onUpdate"]);
const show = defineModel<boolean>();
const error = ref("");
const props = defineProps({
  name: {
    type: String,
    required: true,
  },
});

const contactDetails = ref({
  name: "",
  phone: "",
});

const onSubmit = () => {
  const cleanPhone = (contactDetails.value.phone || "").replace(/[\s\-]/g, "");
  if (
    !z
      .string()
      .regex(/^\+(?:[0-9]){6,14}[0-9]$/)
      .safeParse(cleanPhone).success
  ) {
    error.value = __("Invalid phone number");
    return;
  } else {
    error.value = "";
  }

  createResource({
    url: "frappe.client.set_value",
    params: {
      doctype: "Contact",
      name: props.name,
      fieldname: "phone_nos",
      value: [{ phone: contactDetails.value.phone, is_primary_phone: true }],
    },
    auto: true,
    onSuccess: () => {
      emit("onUpdate");
      toast.success(__("Contact updated successfully."));
      show.value = false;
    },
  });
};

watch(show, (val) => {
  if (val) {
    contactDetails.value = {
      name: props.name,
      phone: "",
    };
  }
});
</script>
