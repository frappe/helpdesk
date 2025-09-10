<template>
  <div
    class="md:mx-10 md:my-4 flex items-center justify-between text-lg font-medium mx-6 mb-4 !mt-8"
  >
    <div class="flex h-8 items-center text-xl font-semibold text-gray-800">
      {{ title }}
    </div>
    <Button
      v-if="title == 'Emails'"
      variant="solid"
      @click="communicationAreaRef?.toggleEmailBox() ?? toggleEmailBox()"
    >
      <template #prefix>
        <FeatherIcon name="plus" class="h-4 w-4" />
      </template>
      <span>{{ "New Email" }}</span>
    </Button>
    <Button
      v-else-if="title == 'Comments'"
      variant="solid"
      @click="communicationAreaRef?.toggleCommentBox() ?? toggleCommentBox()"
    >
      <template #prefix>
        <FeatherIcon name="plus" class="h-4 w-4" />
      </template>
      <span>{{ "New Comment" }}</span>
    </Button>
    <Dropdown v-else-if="title == 'Calls'" :options="callActions" @click.stop>
      <template v-slot="{ open }">
        <Button variant="solid" class="flex items-center gap-1">
          <template #prefix>
            <FeatherIcon name="plus" class="h-4 w-4" />
          </template>
          <span>{{ "New" }}</span>
          <template #suffix>
            <FeatherIcon
              :name="open ? 'chevron-up' : 'chevron-down'"
              class="h-4 w-4"
            />
          </template>
        </Button>
      </template>
    </Dropdown>
    <Dropdown v-else :options="defaultActions" @click.stop>
      <template v-slot="{ open }">
        <Button variant="solid" class="flex items-center gap-1">
          <template #prefix>
            <FeatherIcon name="plus" class="h-4 w-4" />
          </template>
          <span>{{ "New" }}</span>
          <template #suffix>
            <FeatherIcon
              :name="open ? 'chevron-up' : 'chevron-down'"
              class="h-4 w-4"
            />
          </template>
        </Button>
      </template>
    </Dropdown>
  </div>
  <CallLogModal
    v-model="showCallLogModal"
    :ticketId="ticketId"
    @after-insert="refreshTicket"
  />
</template>

<script setup lang="ts">
import { CommentIcon, EmailIcon, PhoneIcon } from "@/components/icons";
import CallLogModal from "@/pages/call-logs/CallLogModal.vue";
import { useTelephonyStore } from "@/stores/telephony";
import { toggleCommentBox, toggleEmailBox } from "@/pages/ticket/modalStates";
import { Dropdown } from "frappe-ui";
import { storeToRefs } from "pinia";
import { computed, h, inject, ref, Ref } from "vue";
defineProps({
  title: {
    type: String,
    required: true,
  },
});

const communicationAreaRef: Ref = inject("communicationArea");
const makeCall = inject<() => void>("makeCall");
const refreshTicket = inject<() => void>("refreshTicket");
const showCallLogModal = ref(false);
const { isCallingEnabled } = storeToRefs(useTelephonyStore());
const ticketId = inject<string>("ticketId");

const defaultActions = computed(() => {
  let actions = [
    {
      icon: h(EmailIcon, { class: "h-4 w-4" }),
      label: "Email",
      onClick: () =>
        communicationAreaRef?.value?.toggleEmailBox() ?? toggleEmailBox(),
    },
    {
      icon: h(CommentIcon, { class: "h-4 w-4" }),
      label: "Comment",
      onClick: () =>
        communicationAreaRef?.value?.toggleCommentBox() ?? toggleCommentBox(),
    },
  ];

  if (isCallingEnabled.value) {
    actions.push(...callActions.value);
  }

  return actions;
});

const callActions = computed(() => {
  let actions = [
    {
      icon: h(PhoneIcon, { class: "h-4 w-4" }),
      label: "Make a Call",
      onClick: () => makeCall(),
    },
    {
      icon: "edit-3",
      label: "Log a Call",
      onClick: () => {
        showCallLogModal.value = true;
      },
    },
  ];
  return actions;
});
</script>

<style scoped></style>
