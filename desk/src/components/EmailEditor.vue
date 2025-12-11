<template>
  <TextEditor
    ref="editorRef"
    :editor-class="[
      'prose-sm max-w-full mx-6 md:mx-10 max-h-[50vh] py-3',
      'min-h-[7rem]',
      getFontFamily(newEmail),
      editable && '!max-h-[35vh] overflow-y-auto',
    ]"
    :content="newEmail"
    :starterkit-options="{ heading: { levels: [2, 3, 4, 5, 6] } }"
    :placeholder="placeholder"
    :editable="editable"
    @change="editable ? (newEmail = $event) : null"
    :extensions="[PreserveVideoControls]"
    :uploadFunction="(file:any)=>uploadFunction(file, doctype, doc.value?.name)"
  >
    <template #top>
      <div class="mx-6 md:mx-10 flex items-center gap-2 border-t py-2.5">
        <span class="text-xs text-gray-500">FROM:</span>
        <SingleSelectEmailInput
          v-model="fromEmailAccount"
          class="flex-1"
          placeholder="Select email account"
        />
      </div>
      <div class="mx-6 md:mx-10 flex items-center gap-2 border-y py-2.5">
        <span class="text-xs text-gray-500">TO:</span>
        <MultiSelectInput
          v-model="toEmailsClone"
          class="flex-1"
          :validate="validateEmail"
          :error-message="(value) => `${value} is an invalid email address`"
        />
        <Button
          :label="'CC'"
          :class="[cc ? 'bg-gray-300 hover:bg-gray-200' : '']"
          @click="toggleCC()"
        />
        <Button
          :label="'BCC'"
          :class="[bcc ? 'bg-gray-300 hover:bg-gray-200' : '']"
          @click="toggleBCC()"
        />
      </div>
      <div
        v-if="showCC || cc"
        class="mx-10 flex items-center gap-2 py-2.5"
        :class="cc || showCC ? 'border-b' : ''"
      >
        <span class="text-xs text-gray-500">CC:</span>
        <MultiSelectInput
          ref="ccInput"
          v-model="ccEmailsClone"
          class="flex-1"
          :validate="validateEmail"
          :error-message="(value) => `${value} is an invalid email address`"
        />
      </div>
      <div
        v-if="showBCC || bcc"
        class="mx-10 flex items-center gap-2 py-2.5"
        :class="bcc || showBCC ? 'border-b' : ''"
      >
        <span class="text-xs text-gray-500">BCC:</span>
        <MultiSelectInput
          ref="bccInput"
          v-model="bccEmailsClone"
          class="flex-1"
          :validate="validateEmail"
          :error-message="(value) => `${value} is an invalid email address`"
        />
      </div>
    </template>
    <!-- <template v-slot:editor="{ _editor }">
      <EditorContent
        :class="[editable && 'max-h-[35vh] overflow-y-auto']"
        :editor="_editor"
      />
    </template> -->
    <template #bottom>
      <!-- Attachments -->
      <div class="flex flex-wrap gap-2 px-10">
        <AttachmentItem
          v-for="a in attachments"
          :key="a.file_url"
          :label="a.file_name"
          :url="!['MOV', 'MP4'].includes(a.file_type) ? a.file_url : null"
        >
          <template #suffix>
            <FeatherIcon
              class="h-3.5"
              name="x"
              @click.self.stop="removeAttachment(a)"
            />
          </template>
        </AttachmentItem>
      </div>
      <!-- TextEditor Fixed Menu -->
      <div
        class="flex justify-between overflow-scroll pl-10 py-2.5 items-center"
      >
        <div class="flex items-center overflow-x-auto w-[60%]">
          <div class="flex gap-1">
            <FileUploader
              :upload-args="{
                doctype: doctype,
                docname: doc.value?.name,
                private: true,
              }"
              @success="
                (f) => {
                  attachments.push(f);
                }
              "
            >
              <template #default="{ openFileSelector }">
                <Button variant="ghost" @click="openFileSelector()">
                  <template #icon>
                    <AttachmentIcon
                      class="h-4"
                      style="color: #000000; stroke-width: 1.5 !important"
                    />
                  </template>
                </Button>
              </template>
            </FileUploader>
            <Button
              variant="ghost"
              @click="showCannedResponseSelectorModal = true"
            >
              <template #icon>
                <EmailIcon
                  class="h-4"
                  style="color: #000000; stroke-width: 1.2"
                />
              </template>
            </Button>
          </div>
          <TextEditorFixedMenu class="ml-1" :buttons="textEditorMenuButtons" />
        </div>
        <div
          class="flex items-center justify-end space-x-2 sm:mt-0 w-[40%] mr-9"
        >
          <Button label="Discard" @click="handleDiscard" />
          <Button
            variant="solid"
            :disabled="emailEmpty"
            :loading="sendMail.loading"
            :label="label"
            @click="
              () => {
                submitMail();
              }
            "
          />
        </div>
      </div>
    </template>
  </TextEditor>
  <CannedResponseSelectorModal
    v-model="showCannedResponseSelectorModal"
    :doctype="doctype"
    @apply="applyCannedResponse"
  />
</template>

<script setup lang="ts">
import {
  AttachmentItem,
  CannedResponseSelectorModal,
  MultiSelectInput,
  SingleSelectEmailInput,
} from "@/components";
import { AttachmentIcon, EmailIcon } from "@/components/icons";
import { useAuthStore } from "@/stores/auth";
import { PreserveVideoControls } from "@/tiptap-extensions";
import {
  getFontFamily,
  isContentEmpty,
  removeAttachmentFromServer,
  textEditorMenuButtons,
  uploadFunction,
  validateEmail,
} from "@/utils";
// import { EditorContent } from "@tiptap/vue-3";
import { useStorage } from "@vueuse/core";
import {
  FileUploader,
  TextEditor,
  TextEditorFixedMenu,
  createResource,
  toast,
  call,
} from "frappe-ui";
import { useOnboarding } from "frappe-ui/frappe";
import { computed, nextTick, ref, watch } from "vue";

const editorRef = ref(null);
const showCannedResponseSelectorModal = ref(false);

const props = defineProps({
  placeholder: {
    type: String,
    default: null,
  },
  label: {
    type: String,
    default: "Send",
  },
  editable: {
    type: Boolean,
    default: true,
  },
  doctype: {
    type: String,
    default: "HD Ticket",
  },
  toEmails: {
    type: Array,
    default: () => [],
  },
  ccEmails: {
    type: Array,
    default: () => [],
  },
  bccEmails: {
    type: Array,
    default: () => [],
  },
});

const label = computed(() => {
  return sendMail.loading ? "Sending..." : props.label;
});

const emit = defineEmits(["submit", "discard"]);
const doc = defineModel();

const newEmail = useStorage("emailBoxContent" + (doc.value?.name || "default"), null);
const { updateOnboardingStep } = useOnboarding("helpdesk");
const { isManager } = useAuthStore();

const attachments = ref([]);
const emailEmpty = computed(() => {
  return isContentEmpty(newEmail.value);
});

const fromEmailAccount = ref<string | null>(null);
const toEmailsClone = ref([...props.toEmails]);
const ccEmailsClone = ref([...props.ccEmails]);
const bccEmailsClone = ref([...props.bccEmails]);
const showCC = ref(false);
const showBCC = ref(false);
const cc = computed(() => (ccEmailsClone.value?.length ? true : false));
const bcc = computed(() => (bccEmailsClone.value?.length ? true : false));
const ccInput = ref(null);
const bccInput = ref(null);

// Fetch email accounts and set default to support@zipcushions.com
const emailAccounts = createResource({
  url: "helpdesk.api.settings.email.get_outgoing_email_accounts",
  auto: true,
  cache: "user-outgoing-email-accounts",
});

// Watch for email accounts to load and set default to support@zipcushions.com
// Use multiple delayed attempts to override SingleSelectEmailInput's auto-select
watch(
  () => emailAccounts.data,
  (accounts: any) => {
    if (accounts && accounts.length > 0) {
      const supportAccount = accounts.find(
        (acc: any) => acc.email_id?.toLowerCase() === "support@zipcushions.com"
      );
      if (supportAccount) {
        // Use multiple delayed attempts to ensure we override SingleSelectEmailInput's auto-select
        // SingleSelectEmailInput auto-selects at ~0ms, so we need to run after that
        const setDefault = () => {
          // Only set if fromEmailAccount is null or matches first account (auto-selected)
          const firstAccount = accounts[0];
          if (
            !fromEmailAccount.value ||
            fromEmailAccount.value === firstAccount?.value
          ) {
            fromEmailAccount.value = supportAccount.value;
          }
        };
        // Try immediately (might be too early)
        setDefault();
        // Try after SingleSelectEmailInput's watch runs
        setTimeout(setDefault, 50);
        setTimeout(setDefault, 150);
        setTimeout(setDefault, 300);
        setTimeout(setDefault, 500);
      }
    }
  },
  { immediate: true }
);

// Also watch fromEmailAccount to catch when SingleSelectEmailInput changes it
watch(
  () => fromEmailAccount.value,
  (currentValue) => {
    if (emailAccounts.data && emailAccounts.data.length > 0 && currentValue) {
      const supportAccount = emailAccounts.data.find(
        (acc: any) => acc.email_id?.toLowerCase() === "support@zipcushions.com"
      );
      if (supportAccount && currentValue !== supportAccount.value) {
        // Check if it's the first account (auto-selected by SingleSelectEmailInput)
        const firstAccount = emailAccounts.data[0];
        if (currentValue === firstAccount?.value) {
          // It was auto-selected, override with support account after a short delay
          setTimeout(() => {
            fromEmailAccount.value = supportAccount.value;
          }, 100);
        }
      }
    }
  }
);


function applyCannedResponse(template) {
  newEmail.value = template.message;
  showCannedResponseSelectorModal.value = false;
}

// Original method: Use reply_via_agent directly
async function sendMailFunction() {
  try {
    // Validate doc exists
    if (!doc.value || !doc.value.name) {
      throw new Error("Document information is not available. Please refresh the page and try again.");
    }
    
    // Validate inputs
    if (!toEmailsClone.value || !Array.isArray(toEmailsClone.value) || toEmailsClone.value.length === 0) {
      throw new Error("Please add at least one recipient email address.");
    }
    
    const recipients = toEmailsClone.value.join(", ");
    const cc = (ccEmailsClone.value && Array.isArray(ccEmailsClone.value)) ? ccEmailsClone.value.join(", ") : "";
    const bcc = (bccEmailsClone.value && Array.isArray(bccEmailsClone.value)) ? bccEmailsClone.value.join(", ") : "";
    const emailAccount = fromEmailAccount.value;
    
    // Validate attachments array
    const attachmentNames = (attachments.value && Array.isArray(attachments.value)) 
      ? attachments.value.map((x: any) => x && x.name).filter(Boolean)
      : [];
    
    // Use custom API endpoint to call reply_via_agent method
    // This avoids the run_doc_method signature issue
    await call("helpdesk.api.ticket.reply_via_agent", {
      ticket_name: doc.value.name,
      message: newEmail.value || "",
      to: recipients,
      cc: cc || undefined,
      bcc: bcc || undefined,
      attachments: attachmentNames,
      email_account: emailAccount || undefined,
    });

    resetState();
    emit("submit");

    if (isManager) {
      updateOnboardingStep("reply_on_ticket");
    }
  } catch (error: any) {
    // Handle error messages
    let errorMessage = "Failed to send email";
    
    if (error) {
      if (typeof error === "string") {
        errorMessage = error;
      } else if (error.message) {
        errorMessage = error.message;
      } else if (error.exc) {
        errorMessage = typeof error.exc === "string" ? error.exc : String(error.exc);
      } else if (error.exc_type) {
        errorMessage = error.exc_type;
      } else if (error.messages && Array.isArray(error.messages) && error.messages.length > 0) {
        errorMessage = error.messages[0];
      } else if (error._error_message) {
        errorMessage = error._error_message;
      }
    }
    
    toast.error(errorMessage);
  }
}

// Create a resource wrapper for the async function
const sendMailLoading = ref(false);
const sendMail = {
  get loading() {
    return sendMailLoading.value;
  },
  submit: async () => {
    sendMailLoading.value = true;
    try {
      await sendMailFunction();
    } finally {
      sendMailLoading.value = false;
    }
  },
};

function submitMail() {
  if (isContentEmpty(newEmail.value)) {
    return false;
  }
  if (!toEmailsClone.value.length) {
    toast.warning(
      "Email has no recipients. Please add at least one email address in the 'TO' field."
    );
    return false;
  }

  sendMail.submit();
}

function toggleCC() {
  showCC.value = !showCC.value;

  showCC.value &&
    nextTick(() => {
      ccInput.value.setFocus();
    });
}

function toggleBCC() {
  showBCC.value = !showBCC.value;
  showBCC.value &&
    nextTick(() => {
      bccInput.value.setFocus();
    });
}

async function removeAttachment(attachment) {
  attachments.value = attachments.value.filter((a) => a !== attachment);
  await removeAttachmentFromServer(attachment.name);
}

function addToReply(
  body: string,
  toEmails: string[],
  ccEmails: string[],
  bccEmails: string[]
) {
  toEmailsClone.value = toEmails;
  ccEmailsClone.value = ccEmails;
  bccEmailsClone.value = bccEmails;
  editorRef.value.editor
    .chain()
    .clearContent()
    .insertContent(body)
    .focus("all")
    .setBlockquote()
    .insertContentAt(0, { type: "paragraph" })
    .focus("start")
    .run();
}

function resetState() {
  newEmail.value = null;
  attachments.value = [];
  fromEmailAccount.value = null;
}

function handleDiscard() {
  attachments.value = [];
  newEmail.value = null;
  fromEmailAccount.value = null;

  toEmailsClone.value = [];
  ccEmailsClone.value = [];
  bccEmailsClone.value = [];
  showCC.value = false;
  showBCC.value = false;

  emit("discard");
}

const editor = computed(() => {
  return editorRef.value.editor;
});

defineExpose({
  addToReply,
  editor,
  submitMail,
  fromEmailAccount,
});
</script>
