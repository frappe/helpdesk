<template>
  <div class="flex flex-col gap-3 px-5 py-3 border-t bg-white">
    <!-- Subject -->
    <FormControl
      v-model="form.subject"
      :label="__('Subject')"
      type="text"
      size="sm"
      variant="subtle"
      :placeholder="__('Enter task subject')"
    />

    <!-- Priority + Status row -->
    <div class="grid grid-cols-2 gap-3">
      <FormControl
        v-model="form.status"
        :label="__('Status')"
        type="select"
        size="sm"
        variant="subtle"
        :options="statusOptions"
      />
      <FormControl
        v-model="form.priority"
        :label="__('Priority')"
        type="select"
        size="sm"
        variant="subtle"
        :options="priorityOptions"
      /
  <div class="flex flex-col">
    <LayoutHeader v-if="ticket.doc?.name">
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" />
      </template>
      <template #right-header>
        <div class="absolute right-0 pr-2">
          <Dropdown :options="dropdownOptions">
            <template #default="{ open }">
              <Button :label="ticket.doc.status">
                <template #prefix>
                  <IndicatorIcon
                    :class="
                      ticketStatusStore.getStatus(ticket.doc.status)
                        ?.parsed_color
                    "
                  />
                </template>
                <template #suffix>
                  <FeatherIcon
                    :name="open ? 'chevron-up' : 'chevron-down'"
                    class="h-4"
                  />
                </template>
              </Button>
            </template>
          </Dropdown>
        </div>
      </template>
    </LayoutHeader>
    <header
      class="flex h-12 items-center justify-between py-[7px] px-3 border-b"
      v-if="ticket.doc?.name"
    >
      <!-- left side -->
      <div class="flex items-center gap-2 max-w-[50%]">
        <AssignTo :hide-label="true" />
      </div>
      <!-- right side -->
      <div class="flex items-center gap-2">
        <CustomActions
          v-if="mobileCustomActions.length"
          :actions="mobileCustomActions"
        />
      </div>
    </header>
    <div v-if="ticket.doc?.name" class="flex flex-1 overflow-x-hidden">
      <div class="flex flex-1 flex-col overflow-x-hidden">
        <div class="flex-1 flex flex-col">
          <Tabs
            :modelValue="tabIndex"
            :tabs="tabs"
            @update:modelValue="changeTabTo"
            class="[&_[role='tab']]:px-0 [&_[role='tablist']]:px-5 [&_[role='tablist']]:gap-7.5"
          >
            <template #tab-panel="{ tab }">
              <div v-if="tab.name === 'details'">
                <!-- ticket contact info -->
                <TicketAgentContact
                  v-if="contact.data"
                  :contact="contact.data"
                  :ticketId="ticket.doc?.name"
                  @email:open="communicationAreaRef.toggleEmailBox()"
                />
                <!-- feedback component -->
                <TicketFeedback
                  v-if="ticket.doc?.feedback_rating"
                  class="border-b px-6 py-3 text-base text-ink-gray-5"
                  :ticket="ticket.doc"
                />
                <!-- SLA Section -->
                <h3 class="px-6 pt-3 font-semibold text-base">
                  {{ __("SLA") }}
                </h3>
                <TicketAgentDetails :ticket="ticket.doc" />
                <!-- Ticket Fields -->
                <h3 class="px-6 pt-3 font-semibold text-base">
                  {{ __("Details") }}
                </h3>
                <TicketAgentFields
                  :ticket="ticketWithFields"
                  @update="
                    ({ field, value }) =>
                      ticket.setValue.submit({ [field]: value })
                  "
                  class="!border-0"
                />
              </div>

              <!-- Rest Activities -->
              <TicketAgentActivities
                v-else
                ref="ticketAgentActivitiesRef"
                :activities="filterActivities(tab.name)"
                :title="tab.label"
                :ticket-status="ticket.doc?.status"
                @update="() => reloadTicket(props.ticketId)"
                @email:reply="
                  (e) => {
                    communicationAreaRef.replyToEmail(e);
                  }
                "
              />
            </template>
          </Tabs>
          <CommunicationArea
            class="sticky bottom-0 z-50 bg-surface-white"
            ref="communicationAreaRef"
            v-model="ticket.doc"
            :ticketId="ticket.doc?.name"
            :to-emails="[ticket.doc.raised_by]"
            :cc-emails="[]"
            :bcc-emails="[]"
            :key="ticket.doc?.name"
            @update="
              () => {
                reloadTicket(props.ticketId);
                tabIndex !== 0 &&
                  ticketAgentActivitiesRef?.scrollToLatestActivity();
              }
            "
          />
        </div>
      </div>
    </div>

    <!-- Start + End date row -->
    <div class="grid grid-cols-2 gap-3">
      <FormControl
        v-model="form.expected_start_date"
        :label="__('Start Date')"
        type="date"
        size="sm"
        variant="subtle"
      />
      <FormControl
        v-model="form.expected_end_date"
        :label="__('End Date')"
        type="date"
        size="sm"
        variant="subtle"
      />
    </div>

    <!-- Description -->
    <div class="flex flex-col gap-1">
      <label class="block text-xs text-gray-600">{{ __("Description") }}</label>
      <TextEditor
        ref="editorRef"
        :editor-class="'prose-sm max-w-none min-h-[5rem] border rounded px-2 py-1.5'"
        :content="form.task_description"
        :editable="true"
        :starterkit-options="{ heading: { levels: [2, 3, 4, 5, 6] } }"
        :placeholder="__('Optional description')"
        @change="(v) => (form.task_description = v)"
      />
    </div>

    <!-- Action buttons -->
    <div class="flex justify-end gap-2">
      <Button :label="__('Discard')" @click="handleDiscard" />
      <Button
        variant="solid"
        :label="__('Create Task')"
        :loading="loading"
        :disabled="isDisabled"
        @click="handleSubmit"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation"
import { isContentEmpty } from "@/utils";
import { Button, FormControl, TextEditor, call, toast } from "frappe-ui";
import { computed, ref } from "vue";
import {
  Breadcrumbs,
  call,
  createResource,
  Dialog,
  Dropdown,
  FormControl,
  Tabs,
  toast,
} from "frappe-ui";
import {
  computed,
  ComputedRef,
  h,
  onMounted,
  onUnmounted,
  PropType,
  provide,
  ref,
  watchEffect,
} from "vue";

import { CommunicationArea, LayoutHeader } from "@/components";
import {
  ActivityIcon,
  CommentIcon,
  DetailsIcon,
  EmailIcon,
  IndicatorIcon,
  PhoneIcon,
} from "@/components/icons";
import { TicketAgentActivities } from "@/components/ticket";

import CustomActions from "@/components/CustomActions.vue";
import AssignTo from "@/components/ticket-agent/AssignTo.vue";
import SetContactPhoneModal from "@/components/ticket/SetContactPhoneModal.vue";
import TicketAgentDetails from "@/components/ticket/TicketAgentDetails.vue";
import TicketAgentFields from "@/components/ticket/TicketAgentFields.vue";
import {
  parseField,
  setupCustomizations,
} from "@/composables/formCustomisation";
import { useScreenSize } from "@/composables/screen";
import { useActiveTabManager } from "@/composables/useActiveTabManager";
import { reloadTicket, useTicket } from "@/composables/useTicket";
import { globalStore } from "@/stores/globalStore";
import { getMeta } from "@/stores/meta";
import { useTelephonyStore } from "@/stores/telephony";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { useUserStore } from "@/stores/user";
import {
  ActivitiesSymbol,
  AssigneeSymbol,
  Customizations,
  CustomizationSymbol,
  FeedbackActivity,
  RecentSimilarTicketsSymbol,
  Resource,
  TabObject,
  TicketContactSymbol,
  TicketSymbol,
  TicketTab,
} from "@/types";
import { HDTicketStatus } from "@/types/doctypes";
import { storeToRefs } from "pinia";
import { useRouter } from "vue-router";

const telephonyStore = useTelephonyStore();
const { isCallingEnabled } = storeToRefs(telephonyStore);

const ticketStatusStore = useTicketStatusStore();
const { getUser } = useUserStore();
const router = useRouter();
const { $dialog } = globalStore();

const ticketAgentActivitiesRef = ref<InstanceType<
  typeof TicketAgentActivities
> | null>(null);
const communicationAreaRef = ref<InstanceType<typeof CommunicationArea> | null>(
  null
);

const subjectInput = ref(null);
const showPhoneModal = ref(false);
const customActions = ref([]);

type ticketId = string;

const props = defineProps({
  ticketId: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(["submit", "discard"]);

const loading = ref(false);

const defaultForm = () => ({
  subject: "",
  status: "Open",
  priority: "Medium",
  task_description: "",
  expected_start_date: "",
  expected_end_date: "",
});

const form = ref(defaultForm());

const isDisabled = computed(() => !form.value.subject?.trim() || loading.value);

const statusOptions = [
  { label: __("Open"), value: "Open" },
  { label: __("Working"), value: "Working" },
  { label: __("Pending Review"), value: "Pending Review" },
  { label: __("Completed"), value: "Completed" },
  { label: __("Cancelled"), value: "Cancelled" },
];

const priorityOptions = [
  { label: __("Low"), value: "Low" },
  { label: __("Medium"), value: "Medium" },
  { label: __("High"), value: "High" },
  { label: __("Urgent"), value: "Urgent" },
];

function handleDiscard() {
  form.value = defaultForm();
  emit("discard");
}

async function handleSubmit() {
  if (!form.value.subject?.trim()) {
    toast.error(__("Subject is required"));
    return;
  }

  if (loading.value) return;
  loading.value = true;

  try {
    await call("helpdesk.helpdesk.doctype.hd_task.hd_task.create_task", {
      ticket: props.ticketId,
      subject: form.value.subject,
      status: form.value.status,
      priority: form.value.priority,
      task_description: isContentEmpty(form.value.task_description)
        ? null
        : form.value.task_description,
      expected_start_date: form.value.expected_start_date || null,
      expected_end_date: form.value.expected_end_date || null,
    });
    toast.success(__("Task created"));
    form.value = defaultForm();
    emit("submit");
  } catch (e: any) {
    toast.error(e?.message || __("Failed to create task"));
  } finally {
    loading.value = false;
  }
}

const editorRef = ref(null);

defineExpose({ editorRef });
</script>
