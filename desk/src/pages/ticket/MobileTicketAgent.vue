<template>
  <div class="flex flex-col">
    <LayoutHeader v-if="ticket.data">
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" />
      </template>
      <template #right-header>
        <div class="absolute right-0 pr-2">
          <Dropdown :options="dropdownOptions">
            <template #default="{ open }">
              <Button :label="ticket.data.status">
                <template #prefix>
                  <IndicatorIcon
                    :class="ticketStatusStore.textColorMap[ticket.data.status]"
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
      v-if="ticket.data"
    >
      <!-- left side -->
      <div class="flex items-center gap-2 max-w-[50%]">
        <div v-if="ticket.data.assignees?.length">
          <component :is="ticket.data.assignees.length == 1 ? 'Button' : 'div'">
            <MultipleAvatar
              :avatars="ticket.data.assignees"
              @click="showAssignmentModal = true"
            />
          </component>
        </div>
        <button
          v-else
          class="rounded bg-gray-100 px-2 py-1.5 text-base text-gray-800"
          @click="showAssignmentModal = true"
        >
          Assign
        </button>
      </div>
      <!-- right side -->
      <div class="flex items-center gap-2">
        <CustomActions
          v-if="ticket.data._customActions"
          :actions="ticket.data._customActions"
        />
      </div>
    </header>
    <div v-if="ticket.data" class="flex flex-1 overflow-x-hidden">
      <div class="flex flex-1 flex-col overflow-x-hidden">
        <div class="flex-1 flex flex-col">
          <Tabs v-model="tabIndex" :tabs="tabs">
            <TabList />
            <TabPanel v-slot="{ tab }" class="h-full">
              <div v-if="tab.name === 'details'">
                <!-- ticket contact info -->
                <TicketAgentContact
                  :contact="ticket.data.contact"
                  @email:open="communicationAreaRef.toggleEmailBox()"
                />
                <!-- feedback component -->
                <TicketFeedback
                  v-if="ticket.data.feedback_rating"
                  class="border-b px-6 py-3 text-base text-gray-600"
                  :ticket="ticket.data"
                />
                <!-- SLA Section -->
                <h3 class="px-6 pt-3 font-semibold text-base">SLA</h3>
                <TicketAgentDetails :ticket="ticket.data" />
                <!-- Ticket Fields -->
                <h3 class="px-6 pt-3 font-semibold text-base">Details</h3>
                <TicketAgentFields
                  :ticket="ticket.data"
                  @update="({ field, value }) => updateTicket(field, value)"
                  class="!border-0"
                />
              </div>

              <!-- Rest Activities -->
              <TicketAgentActivities
                v-else
                ref="ticketAgentActivitiesRef"
                :activities="filterActivities(tab.name)"
                :title="tab.label"
                :ticket-status="ticket.data?.status"
                @update="
                  () => {
                    ticket.reload();
                  }
                "
                @email:reply="
                  (e) => {
                    communicationAreaRef.replyToEmail(e);
                  }
                "
              />
            </TabPanel>
          </Tabs>
          <CommunicationArea
            class="sticky bottom-0 z-50 bg-white"
            ref="communicationAreaRef"
            v-model="ticket.data"
            :to-emails="[ticket.data.raised_by]"
            :cc-emails="[]"
            :bcc-emails="[]"
            :key="ticket.data?.name"
            @update="
              () => {
                ticket.reload();
                tabIndex !== 0 &&
                  ticketAgentActivitiesRef.scrollToLatestActivity();
              }
            "
          />
        </div>
      </div>
    </div>
    <AssignmentModal
      v-if="ticket.data"
      v-model="showAssignmentModal"
      :assignees="ticket.data.assignees"
      :docname="ticketId"
      :team="ticket.data?.agent_group"
      doctype="HD Ticket"
      @update="
        () => {
          ticket.reload();
        }
      "
    />
    <Dialog v-model="showSubjectDialog">
      <template #body-title>
        <h3>Rename</h3>
      </template>
      <template #body-content>
        <FormControl
          v-model="subjectInput"
          :type="'text'"
          size="sm"
          variant="subtle"
          :disabled="false"
          label="New Subject"
        />
      </template>
      <template #actions>
        <Button
          variant="solid"
          :disabled="!subjectInput"
          :loading="isLoading"
          @click="
            () => {
              updateTicket('subject', subjectInput);
              showSubjectDialog = false;
            }
          "
        >
          Confirm
        </Button>
        <Button class="ml-2" @click="showSubjectDialog = false"> Close </Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import {
  Breadcrumbs,
  Dialog,
  Dropdown,
  FormControl,
  TabList,
  TabPanel,
  Tabs,
  call,
  createResource,
  toast,
} from "frappe-ui";
import { computed, h, onMounted, onUnmounted, provide, ref } from "vue";
import { useRouter } from "vue-router";

import {
  AssignmentModal,
  CommunicationArea,
  LayoutHeader,
  MultipleAvatar,
} from "@/components";
import {
  ActivityIcon,
  CommentIcon,
  DetailsIcon,
  EmailIcon,
  IndicatorIcon,
} from "@/components/icons";
import { TicketAgentActivities } from "@/components/ticket";

import TicketAgentDetails from "@/components/ticket/TicketAgentDetails.vue";
import TicketAgentFields from "@/components/ticket/TicketAgentFields.vue";
import { setupCustomizations } from "@/composables/formCustomisation";
import { useScreenSize } from "@/composables/screen";
import { globalStore } from "@/stores/globalStore";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { useUserStore } from "@/stores/user";
import { TabObject, TicketTab } from "@/types";

const ticketStatusStore = useTicketStatusStore();
const { getUser } = useUserStore();

const router = useRouter();
const ticketAgentActivitiesRef = ref(null);
const communicationAreaRef = ref(null);
const subjectInput = ref(null);
const isLoading = ref(false);

const props = defineProps({
  ticketId: {
    type: String,
    required: true,
  },
});

provide("communicationArea", communicationAreaRef);

const { isMobileView } = useScreenSize();
const { $dialog } = globalStore();

const showAssignmentModal = ref(false);
const showSubjectDialog = ref(false);

const ticket = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_one",
  cache: ["Ticket", props.ticketId],
  auto: true,
  params: {
    name: props.ticketId,
  },
  transform: (data) => {
    if (data._assign) {
      data.assignees = JSON.parse(data._assign).map((assignee) => {
        return {
          name: assignee,
          image: getUser(assignee).user_image,
          label: getUser(assignee).full_name,
        };
      });
    }
  },
  onSuccess: (data) => {
    subjectInput.value = ticket.subject;
    setupCustomizations(ticket, {
      doc: data,
      call,
      router,
      toast,
      $dialog,
      updateField,
      createToast: toast.create,
    });
  },
});

function updateField(name: string, value: string, callback = () => {}) {
  updateTicket(name, value);
  callback();
}

const breadcrumbs = computed(() => {
  let items = [{ label: "Tickets", route: { name: "TicketsAgent" } }];
  items.push({
    label: ticket.data?.subject,
    route: { name: "TicketAgent" },
  });
  return items;
});

const dropdownOptions = computed(() =>
  ticketStatusStore.options.map((o) => ({
    label: o,
    value: o,
    onClick: () => updateTicket("status", o),
    icon: () =>
      h(IndicatorIcon, {
        class: ticketStatusStore.textColorMap[o],
      }),
  }))
);

const tabIndex = ref(0);
const tabs: TabObject[] = [
  {
    name: "details",
    label: "Details",
    icon: DetailsIcon,
    condition: () => isMobileView.value,
  },
  {
    name: "activity",
    label: "Activity",
    icon: ActivityIcon,
  },
  {
    name: "email",
    label: "Emails",
    icon: EmailIcon,
  },
  {
    name: "comment",
    label: "Comments",
    icon: CommentIcon,
  },
];

const activities = computed(() => {
  const emailProps = ticket.data.communications.map((email, idx: number) => {
    return {
      subject: email.subject,
      content: email.content,
      sender: { name: email.user.email, full_name: email.user.name },
      to: email.recipients,
      type: "email",
      key: email.creation,
      cc: email.cc,
      bcc: email.bcc,
      creation: email.communication_date || email.creation,
      attachments: email.attachments,
      name: email.name,
      isFirstEmail: idx === 0,
    };
  });

  const commentProps = ticket.data.comments.map((comment) => {
    return {
      name: comment.name,
      type: "comment",
      key: comment.creation,
      commentedBy: comment.commented_by,
      commenter: comment.user.name,
      creation: comment.creation,
      content: comment.content,
      attachments: comment.attachments,
    };
  });

  const historyProps = [...ticket.data.history, ...ticket.data.views].map(
    (h) => {
      return {
        type: "history",
        key: h.creation,
        content: h.action ? h.action : "viewed this",
        creation: h.creation,
        user: h.user.name + " ",
      };
    }
  );

  const sorted = [...emailProps, ...commentProps, ...historyProps].sort(
    (a, b) => new Date(a.creation) - new Date(b.creation)
  );

  const data = [];
  let i = 0;

  while (i < sorted.length) {
    const currentActivity = sorted[i];
    if (currentActivity.type === "history") {
      currentActivity.relatedActivities = [currentActivity];
      for (let j = i + 1; j < sorted.length + 1; j++) {
        const nextActivity = sorted[j];

        if (nextActivity && nextActivity.user === currentActivity.user) {
          currentActivity.relatedActivities.push(nextActivity);
        } else {
          data.push(currentActivity);
          i = j - 1;
          break;
        }
      }
    } else {
      data.push(currentActivity);
    }
    i++;
  }
  return data;
});

function filterActivities(eventType: TicketTab) {
  if (eventType === "activity") {
    return activities.value;
  }
  return activities.value.filter((activity) => activity.type === eventType);
}

function updateTicket(fieldname: string, value: string) {
  isLoading.value = true;
  createResource({
    url: "frappe.client.set_value",
    params: {
      doctype: "HD Ticket",
      name: props.ticketId,
      fieldname,
      value,
    },
    auto: true,
    onSuccess: () => {
      isLoading.value = false;
      ticket.reload();
      toast.success("Ticket updated");
    },
  });
}
onMounted(() => {
  document.title = props.ticketId;
});

onUnmounted(() => {
  document.title = "Helpdesk";
});
</script>
