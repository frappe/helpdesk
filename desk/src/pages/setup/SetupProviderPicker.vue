<template>
  <Transition v-bind="swap">
    <div v-if="screen === 'picker'" key="picker" class="space-y-4">
      <Banner
        v-if="failure"
        :theme="failure.cancelled ? 'gray' : 'red'"
        :title="
          failure.mailbox
            ? __('Couldn\'t connect {0}', [failure.mailbox])
            : __('Couldn\'t connect your mailbox')
        "
        :description="failure.message"
        dismissible
        @dismiss="failure = null"
      >
        <template v-if="failure.adminApproval" #actions>
          <Button
            :label="__('Show what your admin needs')"
            @click="openGmail(failure.mailbox || '')"
          />
        </template>
      </Banner>

      <div
        role="group"
        :aria-label="__('Choose your email provider')"
        class="grid grid-cols-1 gap-2 sm:grid-cols-2"
      >
        <Button
          v-for="p in PROVIDERS"
          :key="p.service"
          variant="outline"
          class="[height:auto] [justify-content:start] px-3 py-2.5 hover:border-outline-gray-4"
          :loading="connecting === p.service"
          :disabled="!!connecting && connecting !== p.service"
          @click="choose(p)"
        >
          <span class="flex w-full min-w-0 items-center gap-3 text-left">
            <img
              v-if="p.logo"
              :src="p.logo"
              alt=""
              class="size-6 shrink-0 object-contain"
            />
            <LucideMail v-else class="size-6 shrink-0 text-ink-gray-6" />
            <span class="min-w-0">
              <span class="block truncate text-base text-ink-gray-8">
                {{ p.label }}
              </span>
              <span class="block truncate text-sm text-ink-gray-5">
                {{ hint(p) }}
              </span>
            </span>
          </span>
        </Button>
      </div>
    </div>

    <form
      v-else-if="screen === 'gmail'"
      key="gmail"
      class="space-y-5"
      novalidate
      @submit.prevent="continueGmail"
    >
      <h2 class="text-md-semibold text-ink-gray-7">
        {{ __("Connect Gmail") }}
      </h2>

      <Alert
        v-if="wrongMailbox"
        theme="red"
        :title="__('You signed in with another Google account')"
        :description="
          __(
            'That isn\'t the address you entered. Sign in with {0}, or set up manually.',
            [gmail]
          )
        "
      />

      <FormControl
        v-model="gmail"
        type="email"
        :label="__('Email address')"
        placeholder="support@example.com"
        :description="
          __('The Gmail or Google Workspace email ID you\'re connecting.')
        "
        :error="gmailInvalid ? __('Enter a valid email address') : undefined"
        @blur="checked = normalizeEmail(gmail)"
        @update:model-value="wrongMailbox = false"
      />

      <Transition v-bind="swap">
        <div
          v-if="gmailKind === 'personal'"
          key="personal"
          class="flex flex-wrap items-center gap-3 rounded-6 bg-surface-gray-1 p-3"
        >
          <div class="flex min-w-0 flex-1 basis-64 flex-col gap-1">
            <span class="text-base-medium text-ink-gray-8">
              {{ __("Personal Gmail connects with an app password") }}
            </span>
            <p class="text-p-base text-ink-gray-6">{{ APP_PASSWORD_STEPS }}</p>
          </div>
          <Button
            variant="outline"
            :href="APP_PASSWORD_LINK"
            icon-right="lucide-arrow-up-right"
            :label="__('How to create one')"
          />
        </div>

        <section
          v-else-if="gmailKind === 'company'"
          key="company"
          class="flex flex-col gap-3 rounded-5 border border-outline-gray-2 p-3"
        >
          <div class="flex items-start gap-3">
            <div class="flex min-w-0 flex-1 flex-col gap-1">
              <h4 class="text-p-base-medium text-ink-gray-8">
                {{ __("Your Google Workspace admin must allow Frappe first") }}
              </h4>
              <p class="text-p-base text-ink-gray-6">
                {{
                  __(
                    "This is a one-time step. Send these steps to your admin, or follow them if you are the admin."
                  )
                }}
              </p>
            </div>
            <Button
              class="-mt-1"
              variant="ghost"
              icon="lucide-copy"
              :tooltip="__('Copy steps for your admin')"
              :aria-label="__('Copy steps for your admin')"
              @click="copy(adminStepsText, __('Steps copied'))"
            />
          </div>
          <ol class="flex list-decimal flex-col gap-5 pl-5">
            <li
              v-for="(s, i) in ADMIN_STEPS"
              :key="i"
              class="text-p-base text-ink-gray-6"
            >
              <div class="flex min-w-0 flex-col">
                <span class="text-p-base-medium text-ink-gray-8">
                  {{ s.title }}
                </span>
                <p class="text-p-base text-ink-gray-6">{{ s.description }}</p>
                <Button
                  v-if="i === 0"
                  class="mt-1.5 self-start"
                  variant="outline"
                  :href="ADMIN_CONSOLE"
                  icon-right="lucide-arrow-up-right"
                  :label="__('Open Google Admin console')"
                />
                <div
                  v-if="i === 1 && clientId"
                  class="mt-1.5 flex items-center gap-1 rounded-4 bg-surface-gray-2 py-1 pl-2 pr-1"
                >
                  <code
                    class="min-w-0 flex-1 truncate text-sm text-ink-gray-8"
                    :title="clientId"
                  >
                    {{ clientId }}
                  </code>
                  <Button
                    variant="ghost"
                    size="sm"
                    icon="lucide-copy"
                    :tooltip="__('Copy client ID')"
                    :aria-label="__('Copy client ID')"
                    @click="copy(clientId, __('Client ID copied'))"
                  />
                </div>
              </div>
            </li>
          </ol>
        </section>
      </Transition>

      <Transition v-bind="grow">
        <ErrorMessage :message="error" />
      </Transition>

      <div class="flex flex-col gap-2">
        <template v-if="gmailKind === 'company'">
          <Button
            type="submit"
            variant="solid"
            theme="gray"
            size="md"
            :label="__('Continue')"
            icon-right="lucide-arrow-up-right"
            :loading="connecting === 'GMail'"
          />
          <Button
            size="md"
            :label="__('Set up manually')"
            @click="manual(normalizeEmail(gmail))"
          />
        </template>
        <template v-else>
          <Button
            type="submit"
            variant="solid"
            theme="gray"
            size="md"
            :label="__('Continue')"
            :disabled="!kindOf(gmail)"
          />
          <p v-if="gmailKind" class="text-center text-p-sm text-ink-gray-6">
            {{ __("Opens the setup form with this address filled in.") }}
          </p>
        </template>
      </div>
    </form>

    <form
      v-else-if="selected"
      key="form"
      class="space-y-6"
      @submit.prevent="create"
    >
      <h2 class="text-md-semibold text-ink-gray-7">{{ formTitle }}</h2>
      <Transition v-bind="grow">
        <div
          v-if="shortcut"
          class="flex items-center gap-3 rounded-5 border border-outline-gray-2 p-3"
        >
          <img
            :src="selected.logo"
            alt=""
            class="size-6 shrink-0 object-contain"
          />
          <div class="min-w-0 flex-1">
            <p class="text-base-medium text-ink-gray-8">
              {{
                workspaceGmail
                  ? __("Sign in with Google instead")
                  : __("Sign in instead")
              }}
            </p>
            <p class="text-p-sm text-ink-gray-6">
              {{
                workspaceGmail
                  ? __(
                      "This is a Google Workspace address, so you don't need an app password."
                    )
                  : __("No password to create.")
              }}
            </p>
          </div>
          <Button
            v-if="workspaceGmail"
            :label="__('Continue')"
            @click="openGmail(normalizeEmail(form.email_id))"
          />
          <Button
            v-else
            :label="hint(selected)"
            icon-right="lucide-arrow-up-right"
            :loading="connecting === selected.service"
            @click="signIn(selected, normalizeEmail(form.email_id))"
          />
        </div>
      </Transition>
      <p v-if="formHelp" class="text-p-sm text-ink-gray-6">
        {{ formHelp }}
      </p>
      <AccountFields
        v-model:form="form"
        class="[&>div:last-child]:hidden"
        @focusout="formEmail = form.email_id"
        :service="selected"
        :error="invalid"
      />
      <Transition v-bind="grow">
        <ErrorMessage :message="error" />
      </Transition>
      <div class="flex justify-end">
        <Button
          type="submit"
          variant="solid"
          theme="gray"
          size="md"
          :label="__('Create')"
          :disabled="workspaceGmail"
          :loading="creating"
        />
      </div>
    </form>
  </Transition>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import type {
  EmailAccountsController,
  OneClickService,
} from "@framework/ui/EmailAccounts";
import { Alert, Button, ErrorMessage, FormControl, toast } from "frappe-ui";
import { useEventListener } from "@vueuse/core";
import { computed, onUnmounted, ref, watch } from "vue";
import {
  emptyForm,
  errorText,
  oauthMessage,
  services,
  validate,
} from "@framework/ui/components/EmailAccounts/services";
import AccountFields from "@framework/ui/components/EmailAccounts/AccountFields.vue";
import Banner from "@framework/ui/components/EmailAccounts/Banner.vue";
import type {
  AccountForm,
  EmailService,
  FieldError,
} from "@framework/ui/components/EmailAccounts/types";
import { validateEmailWithZod } from "@/utils";
import { type Mailbox, normalizeEmail, useSetupFlow } from "./setup";

const { reportError, setStepBack } = useSetupFlow();

const props = defineProps<{
  controller: EmailAccountsController;
  oneClick: Record<string, OneClickService>;
}>();
const emit = defineEmits<{
  connected: [mailbox: Mailbox];
  screen: [screen: Screen];
}>();

type Screen = "picker" | "gmail" | "form";
type Failure = {
  mailbox: string | null;
  message: string;
  cancelled: boolean;
  adminApproval: boolean;
};

const PROVIDERS = services;
const GMAIL = PROVIDERS[0];
const ADMIN_CONSOLE = "https://admin.google.com/ac/owl/list?tab=configuredApps";
const APP_PASSWORD_LINK = "https://support.google.com/accounts/answer/185833";
const APP_PASSWORD_STEPS = __(
  "Turn on 2-Step Verification, then create a 16-character app password in your Google Account."
);
const ADMIN_STEPS = [
  {
    title: __("Open API controls in the Admin console"),
    description: __("Sign in as a Google Workspace admin."),
  },
  {
    title: __("Add Frappe as an app"),
    description: __("Click Configure new app and search for this client ID."),
  },
  {
    title: __("Choose who can connect mailboxes"),
    description: __("All users, or the group that has the support mailbox."),
  },
  {
    title: __("Set access to Trusted"),
    description: __(
      "Select Trusted and click Continue, then click Finish on the review screen."
    ),
  },
];

const screen = ref<Screen>("picker");
watch(screen, (s) => emit("screen", s));
const selected = ref<EmailService | null>(null);
const form = ref<AccountForm>(emptyForm());
const invalid = ref<FieldError>();
const fromGmail = ref(false);
const connecting = ref<string | null>(null);
const creating = ref(false);
const error = ref("");
const failure = ref<Failure | null>(null);

const canSignIn = (p: EmailService) => !!props.oneClick[p.service];
const SIGN_IN_WITH: Record<string, string> = {
  GMail: "Google",
  "Outlook.com": "Microsoft",
  "Yahoo Mail": "Yahoo",
  "Yandex.Mail": "Yandex",
};
function hint(p: EmailService) {
  if (canSignIn(p))
    return __("Sign in with {0}", [SIGN_IN_WITH[p.service] ?? p.label]);
  if (p.outgoingOnly) return __("Sending only");
  if (p.kind === "frappe-mail") return __("API key");
  if (p.kind === "custom") return __("IMAP and SMTP");
  return __("App password");
}
const clientId = computed(() => props.oneClick.GMail?.client_id ?? "");

const gmail = ref("");
const checked = ref("");
const wrongMailbox = ref(false);
function kindOf(value: string) {
  const address = normalizeEmail(value);
  if (!validateEmailWithZod(address)) return null;
  return /@(gmail|googlemail)\.com$/.test(address) ? "personal" : "company";
}
const gmailKind = computed(() => kindOf(checked.value));
const gmailInvalid = computed(
  () => !!checked.value && !gmailKind.value && !kindOf(gmail.value)
);
const adminStepsText = computed(() =>
  [
    __(
      "Please allow Frappe to access Gmail for our team (one-time, about 2 minutes):"
    ),
    `1. ${ADMIN_CONSOLE}`,
    ...ADMIN_STEPS.slice(1).map((s, i) => `${i + 2}. ${s.title}`),
    clientId.value,
  ]
    .filter(Boolean)
    .join("\n")
);

const formEmail = ref("");
const shortcut = computed(() => {
  const p = selected.value;
  if (!p || !canSignIn(p)) return false;
  return p.service !== "GMail" || kindOf(formEmail.value) === "company";
});
const workspaceGmail = computed(
  () => shortcut.value && selected.value?.service === "GMail"
);
const formTitle = computed(() =>
  selected.value?.kind === "custom"
    ? __("New custom email account")
    : __("New {0} account", [selected.value?.label])
);
const formHelp = computed(
  () =>
    selected.value?.help ??
    (selected.value?.outgoingOnly
      ? __("Sends email only. Replies will not become tickets.")
      : "")
);

function choose(p: EmailService) {
  failure.value = null;
  if (p.service === "GMail" && canSignIn(p)) return openGmail("");
  if (canSignIn(p)) return signIn(p);
  open(p);
}

function open(p: EmailService, email = "") {
  selected.value = p;
  form.value = { ...emptyForm(), email_id: email };
  formEmail.value = email;
  invalid.value = undefined;
  error.value = "";
  screen.value = "form";
}

function openGmail(address: string, wrong = false) {
  selected.value = GMAIL;
  gmail.value = address;
  checked.value = address;
  wrongMailbox.value = wrong;
  error.value = "";
  screen.value = "gmail";
}

function manual(address: string) {
  fromGmail.value = true;
  open(GMAIL, address);
}

useEventListener(window, "pageshow", (event: PageTransitionEvent) => {
  if (event.persisted) connecting.value = null;
});

setStepBack({ canGoBack: () => screen.value !== "picker", back });
onUnmounted(() => setStepBack(null));

function back() {
  if (screen.value === "form" && fromGmail.value) {
    fromGmail.value = false;
    screen.value = "gmail";
    return;
  }
  screen.value = "picker";
  selected.value = null;
}

async function signIn(p: EmailService, email?: string) {
  connecting.value = p.service;
  error.value = "";
  try {
    if (await props.controller.connect(p.service, email || undefined)) return;
    open(p, email);
  } catch (e) {
    reportError("email_sign_in", e);
    error.value = errorText(e);
  }
  connecting.value = null;
}

function continueGmail() {
  const address = normalizeEmail(gmail.value);
  const stepsShown = checked.value === address && gmailKind.value === "company";
  checked.value = address;
  if (!gmailKind.value) return;
  if (gmailKind.value === "personal") return manual(address);
  if (stepsShown) signIn(GMAIL, address);
}

async function create() {
  const p = selected.value!;
  const address = normalizeEmail(form.value.email_id);
  const account = {
    ...form.value,
    email_account_name: form.value.email_account_name.trim() || address,
    email_id: address,
  };
  invalid.value = validate(p, account);
  if (invalid.value) return;
  creating.value = true;
  error.value = "";
  try {
    await props.controller.create(p, account);
    connectExisting(address, true);
  } catch (e) {
    if ((e as { exc_type?: string }).exc_type === "DuplicateEntryError") {
      await props.controller.load();
      if (connectExisting(address)) return;
    }
    reportError("email_create", e);
    error.value = /AUTHENTICATIONFAILED|Invalid credentials/i.test(errorText(e))
      ? __(
          "{0} didn't accept this email and password. Check them and try again.",
          [p.label]
        )
      : errorText(e);
  } finally {
    creating.value = false;
  }
}

function connectExisting(address: string, created = false) {
  const account = props.controller.accounts.find(
    (a) => a.email_id.toLowerCase() === address
  );
  if (!account && !created) return false;
  emit("connected", { name: account?.name ?? address, address });
  return true;
}

/** Shows a one-click sign-in this page came back from that did not connect. */
function showSignInFailure(
  result: string,
  mailbox: string | null,
  provider: string | null
) {
  if (result === "wrong_mailbox" && mailbox) return openGmail(mailbox, true);
  const adminApproval = result === "admin_approval";
  failure.value = {
    mailbox,
    message: oauthMessage(result, provider),
    cancelled: result === "cancelled",
    adminApproval: adminApproval && !!mailbox && kindOf(mailbox) === "company",
  };
}

async function copy(text: string, done: string) {
  try {
    await navigator.clipboard.writeText(text);
    toast.success(done);
  } catch {
    toast.error(__("Couldn't copy. Select the text and copy it yourself."));
  }
}

defineExpose({ showSignInFailure });

const swap = {
  enterActiveClass:
    "transition duration-300 ease-out motion-reduce:transition-none",
  enterFromClass: "opacity-0",
  leaveActiveClass: "hidden",
};
const grow = {
  enterActiveClass:
    "overflow-hidden transition-all duration-200 ease-out motion-reduce:transition-none",
  enterFromClass: "!mt-0 max-h-0 opacity-0",
  enterToClass: "max-h-40",
  leaveActiveClass:
    "overflow-hidden transition-all duration-150 ease-in motion-reduce:transition-none",
  leaveFromClass: "max-h-40",
  leaveToClass: "!mt-0 max-h-0 opacity-0",
};
</script>
