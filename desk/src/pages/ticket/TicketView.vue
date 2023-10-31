<template>
  <div v-if="ticket.doc" class="flex flex-col">
    <TicketBreadcrumbs parent="TicketsAgent" :title="ticket.doc?.subject">
      <template #right>
        <TicketAgentActions v-if="authStore.isAgent" />
        <TicketCustomerActions v-else />
      </template>
    </TicketBreadcrumbs>
    <div class="flex grow overflow-hidden">
      <div class="flex grow flex-col">
        <TicketPinnedComments @focus="(v) => (focus = v)" />
        <TicketConversation class="grow" :focus="focus">
          <template #communication-top-right="{ message }">
            <Button
              label="Reply"
              theme="gray"
              variant="outline"
              @click="
                () => {
                  isExpanded = true;
                  mode = Mode.Response;
                  $nextTick(() =>
                    $refs.editor.editor
                      .chain()
                      .clearContent()
                      .insertContent(message)
                      .focus('all')
                      .setBlockquote()
                      .insertContentAt(0, { type: 'paragraph' })
                      .focus('start')
                      .run()
                  );
                }
              "
            />
          </template>
        </TicketConversation>
        <span class="m-5">
          <TicketTextEditor
            ref="editor"
            v-model:attachments="attachments"
            v-model:content="content"
            v-model:expand="isExpanded"
            :mentions="agentStore.dropdown"
            :placeholder="placeholder"
            autofocus
            @clear="() => clear()"
          >
            <template #top-right>
              <span class="flex gap-2">
                <Button
                  v-if="mode === Mode.Response"
                  label="CC"
                  :theme="showCc ? 'blue' : 'gray'"
                  variant="subtle"
                  @click="() => (showCc = !showCc)"
                />
                <Button
                  v-if="mode === Mode.Response"
                  label="BCC"
                  :theme="showBcc ? 'blue' : 'gray'"
                  variant="subtle"
                  @click="() => (showBcc = !showBcc)"
                />
                <TabButtons
                  v-model="mode"
                  :buttons="Object.values(Mode).map((m) => ({ label: m }))"
                />
              </span>
            </template>
            <template v-if="mode == Mode.Response" #top-bottom>
              <div class="my-2.5 space-y-2 border-y py-2">
                <div>
                  <span class="mr-3 text-xs text-gray-500">TO:</span>
                  <Button :label="ticket.doc.raised_by" />
                </div>
                <div v-if="showCc">
                  <span class="inline-flex flex-wrap items-center gap-1">
                    <span class="mr-2 text-xs text-gray-500">CC:</span>
                    <Button
                      v-for="i in cc.split(',').filter(Boolean)"
                      :key="i"
                      :label="i"
                      @click="
                        () =>
                          (cc = cc
                            .split(',')
                            .filter((s) => s !== i)
                            .join(','))
                      "
                    />
                    <FormControl
                      type="text"
                      placeholder="hello@example.com"
                      @keyup.prevent.enter="
                        (event) => {
                          cc = [...cc.split(','), event.target.value].join(',');
                          event.target.value = '';
                        }
                      "
                    />
                  </span>
                </div>
                <div v-if="showBcc">
                  <span class="inline-flex flex-wrap items-center gap-1">
                    <span class="mr-2 text-xs text-gray-500">BCC:</span>
                    <Button
                      v-for="i in bcc.split(',').filter(Boolean)"
                      :key="i"
                      :label="i"
                      @click="
                        () =>
                          (bcc = bcc
                            .split(',')
                            .filter((s) => s !== i)
                            .join(','))
                      "
                    />
                    <FormControl
                      type="text"
                      placeholder="hello@example.com"
                      @keyup.prevent.enter="
                        (event) => {
                          bcc = [...bcc.split(','), event.target.value].join(
                            ','
                          );
                          event.target.value = '';
                        }
                      "
                    />
                  </span>
                </div>
              </div>
            </template>
            <template #bottom-left>
              <Button
                theme="gray"
                variant="ghost"
                @click="showCannedResponses = !showCannedResponses"
              >
                <template #icon>
                  <LucideMessageSquare class="h-4 w-4" />
                </template>
              </Button>
            </template>
            <template #bottom-right>
              <Button
                :label="
                  {
                    Comment: 'Comment',
                    Response: 'Send',
                  }[mode]
                "
                theme="gray"
                variant="solid"
                :disabled="$refs.editor.editor.isEmpty || send.loading"
                @click="() => send.submit()"
              />
            </template>
          </TicketTextEditor>
        </span>
      </div>
      <TicketAgentSidebar />
    </div>
    <TicketCannedResponses
      v-model="showCannedResponses"
      @select="
        (content) => {
          $refs.editor.editor.commands.clearContent();
          $refs.editor.editor.commands.insertContent(content);
        }
      "
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, provide, ref } from "vue";
import {
  createResource,
  createDocumentResource,
  createListResource,
  usePageMeta,
  Button,
  FormControl,
  TabButtons,
} from "frappe-ui";
import { emitter } from "@/emitter";
import { useAgentStore } from "@/stores/agent";
import { useAuthStore } from "@/stores/auth";
import { useError } from "@/composables";
import { Id, Comments, Ticket } from "./symbols";
import TicketAgentActions from "./TicketAgentActions.vue";
import TicketCustomerActions from "./TicketCustomerActions.vue";
import TicketAgentSidebar from "./TicketAgentSidebar.vue";
import TicketBreadcrumbs from "./TicketBreadcrumbs.vue";
import TicketCannedResponses from "./TicketCannedResponses.vue";
import TicketConversation from "./TicketConversation.vue";
import TicketPinnedComments from "./TicketPinnedComments.vue";
import TicketTextEditor from "./TicketTextEditor.vue";

interface P {
  ticketId: string;
}

enum Mode {
  Comment = "Comment",
  Response = "Response",
}

const props = defineProps<P>();
const agentStore = useAgentStore();
const authStore = useAuthStore();
const ticket = createDocumentResource({
  doctype: "HD Ticket",
  cache: ["Ticket", props.ticketId],
  name: props.ticketId,
  whitelistedMethods: {
    assign: "assign_agent",
    markSeen: "mark_seen",
  },
  auto: true,
  onError: useError(),
});
const comments = createListResource({
  doctype: "HD Comment",
  cache: ["Comments", props.ticketId],
  fields: [
    "name",
    "comment_type",
    "content",
    "creation",
    "is_pinned",
    "user",
    {
      attachments: ["file.file_url", "file.file_name"],
    },
  ],
  filters: {
    reference_doctype: "HD Ticket",
    reference_name: props.ticketId,
  },
  orderBy: "creation asc",
  auto: true,
  onError: useError(),
});
provide(Id, props.ticketId);
provide(Comments, comments);
provide(Ticket, ticket);
const editor = ref(null);
const placeholder = "Compose a comment / reply";
const content = ref("");
const attachments = ref([]);
const isExpanded = ref(false);
const cc = ref("");
const bcc = ref("");
const showCc = ref(false);
const showBcc = ref(false);
const mode = ref(Mode.Comment);
const focus = ref("");
const showCannedResponses = ref(false);

emitter.on("update:ticket", () => ticket.reload());

const send = createResource({
  url: "frappe.client.insert",
  debounce: 300,
  makeParams: () => ({
    doc: {
      doctype: "HD Comment",
      attachments: attachments.value,
      comment_type: mode.value == Mode.Comment ? "Private" : "Public",
      content: content.value,
      reference_doctype: "HD Ticket",
      reference_name: props.ticketId,
    },
  }),
  auto: false,
  onSuccess: () => {
    editor.value.editor.commands.clearContent(true);
    attachments.value = [];
    isExpanded.value = false;
    ticket.reload();
  },
  onError: useError(),
});

function clear() {
  editor.value.editor.commands.clearContent(true);
  isExpanded.value = false;
  cc.value = "";
  bcc.value = "";
}

onMounted(() => ticket.markSeen.submit());

usePageMeta(() => {
  return {
    title: ticket.doc?.subject,
  };
});
</script>
