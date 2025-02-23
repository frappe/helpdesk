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
                <TicketAgentDetails
                  :agreement-status="ticket.data.agreement_status"
                  :first-responded-on="ticket.data.first_responded_on"
                  :response-by="ticket.data.response_by"
                  :resolution-date="ticket.data.resolution_date"
                  :resolution-by="ticket.data.resolution_by"
                  :ticket-created-on="ticket.data.creation"
                  :source="ticket.data.via_customer_portal ? 'Portal' : 'Mail'"
                />
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
import { computed, ref, h, watch, onMounted, onUnmounted, provide } from "vue";
import { useStorage } from "@vueuse/core";
import {
  Breadcrumbs,
  Dropdown,
  Tabs,
  TabPanel,
  TabList,
  createResource,
  Dialog,
  FormControl,
} from "frappe-ui";

import {
  LayoutHeader,
  MultipleAvatar,
  AssignmentModal,
  CommunicationArea,
} from "@/components";
import { TicketAgentActivities } from "@/components/ticket";
import {
  ActivityIcon,
  CommentIcon,
  EmailIcon,
  IndicatorIcon,
  DetailsIcon,
} from "@/components/icons";

import { useTicketStatusStore } from "@/stores/ticketStatus";
import { useUserStore } from "@/stores/user";
import { createToast, setupCustomActions } from "@/utils";

const ticketStatusStore = useTicketStatusStore();
const { getUser } = useUserStore();
import { useScreenSize } from "@/composables/screen";
import { TabObject, TicketTab } from "@/types";
import TicketAgentDetails from "@/components/ticket/TicketAgentDetails.vue";
import TicketAgentFields from "@/components/ticket/TicketAgentFields.vue";
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

let storage = useStorage("ticket_agent", {
  showAllActivity: true,
});

const { isMobileView } = useScreenSize();

const showFullActivity = ref(storage.value.showAllActivity);
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
    subjectInput.value = data.subject;
    setupCustomActions(data, {
      doc: data,
    });
  },
});

const breadcrumbs = computed(() => {
  let items = [{ label: "Tickets", route: { name: "TicketsAgent" } }];
  items.push({
    label: ticket.data?.subject,
    route: { name: "TicketAgent" },
  });
  return items;
});

watch(
  () => showFullActivity.value,
  (value) => {
    storage.value.showAllActivity = value;
  }
);

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
  const emailProps = ticket.data.communications.map((email) => {
    return {
      type: "email",
      key: email.creation,
      sender: { name: email.user.email, full_name: email.user.name },
      to: email.recipients,
      cc: email.cc,
      bcc: email.bcc,
      creation: email.creation,
      subject: email.subject,
      attachments: email.attachments,
      content: email.content,
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
    };
  });

  if (!showFullActivity.value) {
    return [...emailProps, ...commentProps].sort(
      (a, b) => new Date(a.creation) - new Date(b.creation)
    );
  }

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
      currentActivity.relatedActivities = [];
      for (let j = i + 1; j < sorted.length + 1; j++) {
        const nextActivity = sorted[j];
        if (nextActivity && nextActivity.type === "history") {
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
      createToast({
        title: "Ticket updated",
        icon: "check",
        iconClasses: "text-green-600",
      });
    },
    onError: (e) => {
      isLoading.value = false;

      const title =
        e.messages && e.messages.length > 0
          ? e.messages[0]
          : "Failed to update ticket";

      createToast({
        title,
        icon: "x",
        iconClasses: "text-red-600",
      });
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
