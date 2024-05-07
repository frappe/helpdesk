<template>
  <div v-if="ticket.data" class="flex flex-col">
    <TicketBreadcrumbs parent="TicketsAgent">
      <template #right>
        <TicketAgentActions />
      </template>
    </TicketBreadcrumbs>
    <div class="flex grow overflow-auto">
      <div class="flex grow flex-col">
        <TicketPinnedComments @focus="(v) => (focus = v)" />
        <TicketConversation class="grow" :focus="focus">
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
                <Icon icon="lucide:reply" />
              </template>
            </Button>
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
                  @click="() => { showCc = !showCc; refreshCcList(); }"
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
                <div class="inline-flex flex-wrap items-center gap-1">
                  <span class="mr-2 text-xs text-gray-500">TO:</span>
                  <!-- <Button :label="ticket.data.raised_by" /> -->
                  <Button
                      v-for="i in recipient.split(',').filter(Boolean)"
                      :key="i"
                      :label="i"
                      @click="
                        () =>
                          (recipient = recipient
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
                          recipient = [...recipient.split(','), event.target.value].join(
                            ','
                          );
                          event.target.value = '';

                        }
                        
                      "
                    />
                    <Button label="Get Emails" @click="showPopup" theme='blue'/>
                    <Dialog v-model="open" :options="{ title: 'Fetch Emails', size: 'lg' }">
                      <template #body-content>
                        <div class="w-full space-y-1">
                            <div>
                              <span class="mb-2 block text-sm leading-4 text-gray-700">
                                Select To
                              </span>
                            </div>
                            <Autocomplete
                              :value="selectedCustomer"
                              :resource-options="{
                                url: 'helpdesk.helpdesk.doctype.hd_ticket.api.get_recipient_list_from_tickets',
                                inputMap: (query) => {
                                  return {
                                    filters: [['raised_by', 'like', `%${query}%`]],
                                  };
                                },
                                responseMap: (res) => {
                                  return res.map((d) => {
                                    return {
                                      label: d,
                                      value: d
                                    };
                                  });
                                },
                              }"
                              @change="
                                (item) => {
                                  if (!item) {
                                    return;
                                  }
                                  selectedCustomer = item.value;
                                  recipient = [...recipient.split(','), selectedCustomer].join(',');
                                  //selectedCustomer = ''; // Clear the selected email after adding it to the recipients
                                }
                              "
                            />
                            <!-- </div> -->
                            <div>
                              <span class="mb-2 block text-sm leading-4 text-gray-700">
                                Select CC
                              </span>
                            </div>
                            <Autocomplete
                              :value="selectedCC"
                              :resource-options="{
                                url: 'helpdesk.helpdesk.doctype.hd_ticket.api.get_recipient_list_from_tickets',
                                inputMap: (query) => {
                                  return {
                                    filters: [['raised_by', 'like', `%${query}%`]],
                                  };
                                },
                                responseMap: (res) => {
                                  return res.map((d) => {
                                    return {
                                      label: d,
                                      value: d
                                    };
                                  });
                                },
                              }"
                              @change="
                                (item) => {
                                  if (!item) {
                                    return;
                                  }
                                  selectedCC = item.value;
                                  cc = [...cc.split(','), selectedCC].join(',');
                                  //selectedCustomer = ''; // Clear the selected email after adding it to the recipients
                                }
                              "
                            />
                            </div>
                        </template>
                    </Dialog>
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
                  <Icon icon="lucide:message-square" />
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
                :disabled="$refs.editor.editor.isEmpty || resource.loading"
                @click="() => resource.submit()"
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
import { computed, onBeforeUnmount, onMounted, provide, ref, watchEffect } from "vue";
import {
  createResource,
  usePageMeta,
  Button,
  FormControl,
  TabButtons,
} from "frappe-ui";
import { Icon } from "@iconify/vue";
import { emitter } from "@/emitter";
import { socket } from "@/socket";
import { useAgentStore } from "@/stores/agent";
import { useError } from "@/composables/error";
import TicketAgentActions from "./TicketAgentActions.vue";
import TicketAgentSidebar from "./TicketAgentSidebar.vue";
import TicketBreadcrumbs from "./TicketBreadcrumbs.vue";
import TicketCannedResponses from "./TicketCannedResponses.vue";
import TicketConversation from "./TicketConversation.vue";
import TicketPinnedComments from "./TicketPinnedComments.vue";
import TicketTextEditor from "./TicketTextEditor.vue";
import { ITicket } from "./symbols";



interface P {
  ticketId: string;
}

enum Mode {
  Comment = "Comment",
  Response = "Response",
}

const props = defineProps<P>();
const agentStore = useAgentStore();
const ticket = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_one",
  cache: ["Ticket", props.ticketId],
  auto: true,
  params: {
    name: props.ticketId,
  },
});
provide(ITicket, ticket);
const editor = ref(null);
const placeholder = "Compose a comment / reply";
const content = ref("");
const attachments = ref([]);
const isExpanded = ref(false);
const recipient = ref("");
const cc = ref("");
const bcc = ref("");
const showCc = ref(false);
const showBcc = ref(false);
const mode = ref(Mode.Comment);
const focus = ref("");
const showCannedResponses = ref(false);


const open = ref(false);
const customer = ref("");

function showPopup(){
  open.value = true
}

createResource({
  url: "run_doc_method",
  params: {
    dt: "HD Ticket",
    dn: props.ticketId,
    method: "mark_seen",
  },
  auto: true,
});

emitter.on("update:ticket", () => ticket.reload());

const comment = createResource({
  url: "run_doc_method",
  debounce: 300,
  makeParams: () => ({
    dt: "HD Ticket",
    dn: props.ticketId,
    method: "new_comment",
    args: {
      content: content.value,
    },
  }),
  onSuccess: () => {
    clear();
    emitter.emit("update:ticket");
  },
  onError: useError({ title: "Error adding comment" }),
});

const response = createResource({
  url: "run_doc_method",
  debounce: 300,
  makeParams: () => ({
    dt: "HD Ticket",
    dn: props.ticketId,
    method: "reply_via_agent",
    args: {
      attachments: attachments.value.map((x) => x.name),
      recipient: recipient.value,
      cc: cc.value,
      bcc: bcc.value,
      message: content.value,
    },
  }),
  onSuccess: () => {
    clear();
    emitter.emit("update:ticket");
  },
});

const resource = computed(() => {
  return {
    Comment: comment,
    Response: response,
  }[mode.value];
});

function clear() {
  editor.value.editor.commands.clearContent(true);
  isExpanded.value = false;
  cc.value = "";
  bcc.value = "";
}

const events = [
  "helpdesk:new-communication",
  "helpdesk:new-ticket-comment",
  "helpdesk:delete-ticket-comment",
  "helpdesk:ticket-update",
  "helpdesk:update-ticket-assignee",
  "helpdesk:ticket-assignee-update",
];

onMounted(() =>
  events.forEach((e) =>
    socket.on(e, (d) => {
      const id = d.name || d.id;
      const shouldReload = !id || id == props.ticketId;
      if (shouldReload) ticket.reload();
    })
  )
);
onBeforeUnmount(() => events.forEach((e) => socket.off(e)));

usePageMeta(() => {
  return {
    title: ticket.data?.subject,
  };
});

// function fetchDefaultRecipient() {
//   return new Promise((resolve, reject) => {
//     const recipient_list = [];
//     watchEffect(() => {
//       const details = ticket.data?.communications;
//       if (details != undefined) {
        
//         // const item = JSON.parse(JSON.stringify(details));
//         details.forEach(d => {
//           recipient_list.push(d.sender);
//           recipient_list.push(d.recipients);             
//         });
//         const uniqueToList = [...new Set(recipient_list)];
//         // console.log(uniqueToList);
        
//         resolve(uniqueToList);
//       }
//     });
//   });
// }
function fetchDefaultRecipient() {
  return new Promise((resolve, reject) => {
    const recipient_set = new Set(); // Use a Set to automatically remove duplicates
    watchEffect(() => {
      const details = ticket.data?.communications;
      if (details !== undefined) {
        const result = Array.isArray(details[details.length - 1]) ? details[details.length - 1] : [details[details.length - 1]];

        result.forEach(d => {
          recipient_set.add(d['sender'])
          // If recipients is an array, spread it to add each email individually to the Set
          if (Array.isArray(d['recipients'])) {
            d['recipients'].forEach(email => {
              recipient_set.add(email.trim()); // Trim to remove any leading/trailing spaces
            });
          } else if (typeof d.recipients === 'string') {
            // If recipients is a string, split it by comma and add each email to the Set
            d['recipients'].split(',').forEach(email => {
              recipient_set.add(email.trim()); // Trim to remove any leading/trailing spaces
            });
          }
        })
        const uniqueToList = Array.from(recipient_set); // Convert Set back to array
        resolve(uniqueToList);
      }
    });
  });
}

function fetchDefaultcc() {
  return new Promise((resolve, reject) => {
    var fetch_cc_tag = "";
    const cc_list = [];
    
    watchEffect(() => {
      const details = ticket.data?.communications;
      if (details != undefined) {
        
        const item = JSON.parse(JSON.stringify(details));
        const result = null
        if (item !== undefined) {
          const result = Array.isArray(item[item.length - 1]) ? item[item.length - 1] : [item[item.length - 1]];
          // console.log(result['cc']);
          
          result.forEach(x => {
            fetch_cc_tag += x['cc']
          })
        
            var include_regular_expression_in_cc = false
            const re = /[^< ]+(?=>)/g;
            const matchedcc = fetch_cc_tag.match(re) || []; // Handle case when there are no matches
            matchedcc.forEach(function(email) {
                include_regular_expression_in_cc = true
                cc_list.push(email);
            });

            if(!include_regular_expression_in_cc){
              result.forEach(x => {
                cc_list.push(x['cc']);
              })
            }
            const UniqueCCList = [...new Set(cc_list)];
            resolve(UniqueCCList);
          // });
        }
        // location.reload()
        
       
      }
    });
  });
}


onMounted(async () => {
  try {
    const recipient_ = await fetchDefaultRecipient() as string[]; // Type assertion
    recipient.value = recipient_.join(',');
    const ccList = await fetchDefaultcc() as string[]; // Type assertion
    cc.value = ccList.join(',');
  } catch (error) {
    console.error(error);
  }
});
function refreshCcList() {
  fetchDefaultcc()
    .then((ccList) => {
      cc.value = ccList.join(',');
    })
    .catch((error) => {
      console.error('Error fetching CC list:', error);
    });
}

function addSelectedToCC() {
  cc.value = [...cc.split(','), selectedEmail].join(',');
  selectedEmail = ''; // Clear the selected email after adding it to the CC list
}
</script>
