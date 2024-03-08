<template>
  <div v-for="emailProp in emailProps" :key="emailProp.creation" class="pb-6">
    <div class="grid grid-cols-[30px_minmax(auto,_1fr)] gap-4 px-10">
      <div
        class="relative flex justify-center before:absolute before:left-[50%] before:top-0 before:-z-10 before:border-l before:border-gray-200"
        :class="[
          'before:h-full',
          'after:translate-y-[calc(-50% - 4px)] after:absolute after:bottom-9 after:left-[50%] after:top-0 after:-z-10 after:w-8 after:rounded-bl-xl after:border-b after:border-l after:border-gray-200',
        ]"
      >
        <div
          class="z-10 flex h-7 w-7 items-center justify-center rounded-full bg-gray-100"
          :class="{
            'mt-3': [
              'communication',
              'incoming_call',
              'outgoing_call',
            ].includes('communication'),
            'bg-white': ['added', 'removed', 'changed'].includes('added'),
          }"
        >
          <component
            :is="EmailAtIcon"
            :class="
              ['added', 'removed', 'changed'].includes('added')
                ? 'text-gray-600'
                : 'text-gray-800'
            "
          />
        </div>
      </div>
      <EmailBox v-bind="emailProp" />
    </div>
  </div>
</template>

<script setup lang="ts">
import EmailAtIcon from "@/components/icons/EmailAtIcon.vue";
import { defineModel } from "vue";
import { EmailBox } from "@/components";

const doc = defineModel();
const emails = doc.value.data.communications;
const comments = doc.value.data.comments;

const emailProps = emails.map((email) => {
  let obj = {};
  obj.sender = { name: email.user.email, full_name: email.user.name };
  obj.to = email.recipients;
  obj.cc = email.cc;
  obj.bcc = email.bcc;
  obj.creation = email.creation;
  obj.subject = email.subject;
  obj.attachments = email.attachments;
  obj.content = email.content;
  return obj;
});

defineProps({
  title: {
    type: String,
    default: "Activity",
  },
});
</script>
