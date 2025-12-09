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
    :uploadFunction="(file:any)=>uploadFunction(file, doctype, modelValue?.name)"
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
                docname: modelValue?.name,
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
import { useUserStore } from "@/stores/user";
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
import { computed, nextTick, ref } from "vue";

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

const newEmail = useStorage("emailBoxContent" + doc.value.name, null);
const { updateOnboardingStep } = useOnboarding("helpdesk");
const { isManager, userId, username } = useAuthStore();
const { getUser, users } = useUserStore();

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

function applyCannedResponse(template) {
  newEmail.value = template.message;
  showCannedResponseSelectorModal.value = false;
}

// Use CRM approach: create Communication first, then send via API
// This avoids the reply_via_agent method signature issue completely
async function sendMailFunction() {
  try {
    // Validate inputs
    if (!toEmailsClone.value || !Array.isArray(toEmailsClone.value) || toEmailsClone.value.length === 0) {
      throw new Error("Please add at least one recipient email address.");
    }
    
    const recipients = toEmailsClone.value.join(", ");
    const subject = doc.value.subject ? `Re: ${doc.value.subject}` : "No Subject";
    const cc = (ccEmailsClone.value && Array.isArray(ccEmailsClone.value)) ? ccEmailsClone.value.join(", ") : "";
    const bcc = (bccEmailsClone.value && Array.isArray(bccEmailsClone.value)) ? bccEmailsClone.value.join(", ") : "";
    const emailAccount = fromEmailAccount.value;

    // Get current user's email address from User doctype
    // Frappe's email.make needs a valid email address, not username
    // Use userId, fallback to username, then to frappe.session.user
    const frappeUser = typeof window !== 'undefined' && (window as any).frappe?.session?.user;
    let userIdentifier = (userId && userId.value) || (username && username.value) || frappeUser;
    let senderEmail: string | undefined = undefined;
    let senderFullName: string | undefined = undefined;
    
    // Defensive check: ensure we have a user identifier
    if (!userIdentifier || typeof userIdentifier !== "string") {
      throw new Error("User ID is not available. Please refresh the page and try again.");
    }
    
    // Fetch user's email from User doctype
    try {
      const userInfo = await call("frappe.client.get", {
        doctype: "User",
        name: userIdentifier,
      });
      if (userInfo && userInfo.email) {
        senderEmail = userInfo.email;
        senderFullName = userInfo.full_name || undefined;
      } else if (userInfo && userInfo.name) {
        // Fallback to name if email not available
        senderEmail = userInfo.name;
        senderFullName = userInfo.full_name || undefined;
      }
    } catch (e) {
      // If userIdentifier is already an email, use it
      if (userIdentifier.includes("@")) {
        senderEmail = userIdentifier;
      } else {
        // userIdentifier is username, not email - try to get from users list
        if (users && users.data && Array.isArray(users.data)) {
          const currentUser = users.data.find((u: any) => u && u.name === userIdentifier);
          if (currentUser && currentUser.email) {
            senderEmail = currentUser.email;
            senderFullName = currentUser.full_name || undefined;
          }
        }
      }
    }
    
    // Final validation: ensure we have a valid sender email
    if (!senderEmail || typeof senderEmail !== "string" || !senderEmail.includes("@")) {
      throw new Error("Unable to determine sender email address. Please ensure your user account has a valid email address configured.");
    }

    // Step 1: Create communication without sending
    // Validate attachments array
    const attachmentNames = (attachments.value && Array.isArray(attachments.value)) 
      ? attachments.value.map((x: any) => x && x.name).filter(Boolean)
      : [];
    
    let result;
    try {
      result = await call("frappe.core.doctype.communication.email.make", {
        recipients: recipients,
        attachments: attachmentNames,
        cc: cc || undefined,
        bcc: bcc || undefined,
        subject: subject,
        content: newEmail.value || "",
        doctype: props.doctype,
        name: doc.value?.name,
        send_email: false, // Don't send yet, we need to set email_account first
        sender: senderEmail,
        sender_full_name: senderFullName || undefined,
      });
    } catch (apiError: any) {
      // Extract error message from various possible formats
      let errorMsg = "Failed to create communication";
      if (apiError) {
        if (typeof apiError === "string") {
          errorMsg = apiError;
        } else if (apiError.message) {
          errorMsg = apiError.message;
        } else if (apiError.exc) {
          errorMsg = typeof apiError.exc === "string" ? apiError.exc : JSON.stringify(apiError.exc);
        } else if (apiError.exc_type) {
          errorMsg = apiError.exc_type;
        } else if (apiError.messages && Array.isArray(apiError.messages) && apiError.messages.length > 0) {
          errorMsg = apiError.messages[0];
        } else if (apiError._error_message) {
          errorMsg = apiError._error_message;
        }
      }
      throw new Error(errorMsg);
    }

    // Step 2: Send the email with the selected email_account (if any)
    if (!result || !result.name) {
      throw new Error("Failed to create communication: No communication name returned");
    }
    
    try {
      await call("helpdesk.api.settings.email.send_communication_email", {
        communication_name: result.name,
        email_account: emailAccount || undefined,
      });
    } catch (sendError: any) {
      // Extract error message from various possible formats
      let errorMsg = "Failed to send email";
      if (sendError) {
        if (typeof sendError === "string") {
          errorMsg = sendError;
        } else if (sendError.message) {
          errorMsg = sendError.message;
        } else if (sendError.exc) {
          errorMsg = typeof sendError.exc === "string" ? sendError.exc : JSON.stringify(sendError.exc);
        } else if (sendError.exc_type) {
          errorMsg = sendError.exc_type;
        } else if (sendError.messages && Array.isArray(sendError.messages) && sendError.messages.length > 0) {
          errorMsg = sendError.messages[0];
        } else if (sendError._error_message) {
          errorMsg = sendError._error_message;
        }
      }
      throw new Error(errorMsg);
    }

    resetState();
    emit("submit");

    if (isManager) {
      updateOnboardingStep("reply_on_ticket");
    }
  } catch (error: any) {
    // Handle different error formats - be very defensive
    let errorMessage = "Failed to send email";
    
    try {
      if (error) {
        if (typeof error === "string") {
          errorMessage = error;
        } else if (error.message) {
          errorMessage = error.message;
        } else if (error.exc) {
          // exc might be a string or object
          if (typeof error.exc === "string") {
            errorMessage = error.exc;
          } else {
            try {
              errorMessage = JSON.stringify(error.exc);
            } catch {
              errorMessage = String(error.exc);
            }
          }
        } else if (error.exc_type) {
          errorMessage = error.exc_type;
        } else if (error.messages && Array.isArray(error.messages) && error.messages.length > 0) {
          errorMessage = error.messages[0];
        } else if (error._error_message) {
          errorMessage = error._error_message;
        } else {
          // Last resort - try to stringify the whole error
          try {
            errorMessage = JSON.stringify(error);
          } catch {
            errorMessage = String(error) || "Failed to send email";
          }
        }
      }
    } catch (parseError) {
      // If even error parsing fails, use a safe fallback
      errorMessage = "Failed to send email. Please try again or contact support if the issue persists.";
    }
    
    toast.error(errorMessage);
    // Don't re-throw to prevent further error propagation
    // The error is already logged and shown to user
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

  ccEmailsClone.value = [];
  bccEmailsClone.value = [];
  ccEmailsClone.value = [];
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
