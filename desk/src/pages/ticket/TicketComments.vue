<template>
  <div class="flex flex-col">
    <TicketConversation :focus="focus" class="grow">
      <template #communication-top-right="{ message }">
        <Button
          theme="gray"
          variant="ghost"
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
        >
          <template #icon>
            <LucideReply class="h-4 w-4" />
          </template>
        </Button>
      </template>
    </TicketConversation>
    <div class="sticky bottom-0 backdrop-blur-lg">
      <TicketTextEditor
        v-if="isExpanded"
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
            <Tooltip
              v-if="mode === Mode.Comment"
              text="Private comments can only be seen by other agents"
            >
              <Badge label="Private" theme="green" variant="outline" />
            </Tooltip>
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
                      bcc = [...bcc.split(','), event.target.value].join(',');
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
            label="Submit"
            theme="gray"
            variant="solid"
            :disabled="$refs.editor.editor.isEmpty || send.loading"
            @click="() => send.submit()"
          />
        </template>
      </TicketTextEditor>
      <div v-else class="space-x-2 px-5 py-3">
        <Button
          label="Reply"
          theme="gray"
          variant="solid"
          @click="
            () => {
              mode = Mode.Response;
              isExpanded = true;
            }
          "
        />
        <Button
          label="Comment"
          theme="gray"
          variant="subtle"
          @click="
            () => {
              mode = Mode.Comment;
              isExpanded = true;
            }
          "
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { inject, ref } from 'vue';
import { createResource, Badge, Tooltip, TabButtons } from 'frappe-ui';
import { useAgentStore } from '@/stores/agent';
import { useError } from '@/composables';
import { Id, Ticket } from './symbols';
import TicketConversation from './TicketConversation.vue';
import TicketTextEditor from './TicketTextEditor.vue';

enum Mode {
  Comment = 'Comment',
  Response = 'Response',
}

const ticketId = inject(Id);
const ticket = inject(Ticket);
const agentStore = useAgentStore();
const placeholder = 'Compose a comment / reply';
const content = ref('');
const attachments = ref([]);
const showCc = ref(false);
const showBcc = ref(false);
const mode = ref(Mode.Comment);
const focus = ref('');
const editor = ref(null);
const isExpanded = ref(false);
const cc = ref('');
const bcc = ref('');
const send = createResource({
  url: 'frappe.client.insert',
  debounce: 300,
  makeParams: () => ({
    doc: {
      doctype: 'HD Comment',
      attachments: attachments.value,
      comment_type: mode.value == Mode.Comment ? 'Private' : 'Public',
      content: content.value,
      reference_doctype: 'HD Ticket',
      reference_name: ticketId,
    },
  }),
  auto: false,
  onSuccess: () => {
    editor.value.editor.commands.clearContent(true);
    attachments.value = [];
    isExpanded.value = false;
  },
  onError: useError(),
});

function clear() {
  editor.value.editor.commands.clearContent(true);
  isExpanded.value = false;
  cc.value = '';
  bcc.value = '';
}
</script>
