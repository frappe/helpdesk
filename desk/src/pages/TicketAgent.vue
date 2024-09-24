<template>
  <div class="flex flex-col">
    <LayoutHeader v-if="ticket.data">
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" />
      </template>
      <template #right-header>
        <CustomActions
          v-if="ticket.data._customActions"
          :actions="ticket.data._customActions"
        />
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
      </template>
    </LayoutHeader>
    <div v-if="ticket.data" class="flex h-screen overflow-hidden">
      <div class="flex flex-1 flex-col">
        <!-- ticket activities -->
        <div class="overflow-y-auto">
          <Tabs
            v-model="tabIndex"
            v-slot="{ tab }"
            :tabs="tabs"
            class="flex flex-col flex-1"
          >
            <TicketAgentActivities
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
          </Tabs>
        </div>
        <CommunicationArea
          ref="communicationAreaRef"
          v-model="ticket.data"
          :to-emails="[ticket.data?.raised_by]"
          :cc-emails="[]"
          :bcc-emails="[]"
          @update="
            () => {
              ticket.reload();
              ticketAgentActivitiesRef.scrollToLatestActivity();
            }
          "
        />
      </div>
      <TicketAgentSidebar
        :ticket="ticket.data"
        @update="({ field, value }) => updateTicket(field, value)"
        @email:open="(e) => communicationAreaRef.toggleEmailBox()"
      />
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
import { computed, ref, h, watch, onMounted, onUnmounted } from "vue";
import { useStorage } from "@vueuse/core";
import {
  Breadcrumbs,
  Dropdown,
  createResource,
  Dialog,
  FormControl,
  Tabs,
} from "frappe-ui";

import {
  LayoutHeader,
  MultipleAvatar,
  AssignmentModal,
  CommunicationArea,
} from "@/components";
import { TicketAgentActivities, TicketAgentSidebar } from "@/components/ticket";
import {
  IndicatorIcon,
  CommentIcon,
  ActivityIcon,
  EmailIcon,
} from "@/components/icons";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { useUserStore } from "@/stores/user";
import { createToast, setupCustomActions } from "@/utils";
import { TabObject, TicketTab } from "@/types";
import { provide } from "vue";
import { nextTick } from "vue";

const ticketStatusStore = useTicketStatusStore();
const { getUser } = useUserStore();
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
      subject: email.subject,
      content: email.content,
      sender: { name: email.user.email, full_name: email.user.name },
      to: email.recipients,
      type: "email",
      key: email.creation,
      cc: email.cc,
      bcc: email.bcc,
      creation: email.creation,
      attachments: email.attachments,
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
