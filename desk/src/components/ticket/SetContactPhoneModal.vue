<template>
  <Dialog
    v-model="show"
    :options="{
      title: __('Set Phone Number'),
      actions: [
        {
          label: __('Set Phone Number'),
          variant: 'solid',
          onClick: onSubmit,
        },
      ],
    }"
  >
    <template #body-content>
      <div>
        <div class="text-base text-ink-gray-6">
          {{ __("{0} does not have a phone number, set one to call them.", [contactDetails.name]) }}
        </div>
        <div class="flex flex-col gap-2 mt-6">
          <FormControl
            v-model="contactDetails.phone"
            :label="__('Phone')"
            type="text"
            size="sm"
            variant="subtle"
            placeholder="+918956895623"
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
  if (
    !z
      .string()
      .regex(/^\+(?:[0-9]){6,14}[0-9]$/)
      .safeParse(contactDetails.value.phone).success
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
      toast.success(__("Contact updated"));
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
