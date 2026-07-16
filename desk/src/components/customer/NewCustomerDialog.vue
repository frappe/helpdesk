<template>
  <Dialog
    v-model:open="model"
    :title="__('Create Customer')"
    size="lg"
    @after-leave="reset"
  >
    <template #default>
      <div>
        <div class="flex flex-col gap-3">
          <ImageAvatar
            v-model="state.image"
            :label="__('Logo')"
            :fallback-label="state.name || __('Customer')"
            shape="square"
          />

          <FormControl
            class="[&_p]:text-p-xs"
            type="text"
            :label="__('Name')"
            :required="true"
            placeholder="Frappe"
            v-model="state.name"
          />

          <div class="grid grid-cols-2 gap-4">
            <FormControl
              class="[&_p]:text-p-xs [&_[data-slot=trigger]]:w-full [&_[data-slot=trigger]]:!text-ink-gray-8"
              type="select"
              :label="__('Customer Type')"
              :options="customerTypeOptions"
              v-model="state.customerType"
            />
            <Link
              :label="__('Country')"
              placeholder="India"
              doctype="Country"
              v-model="state.country"
            >
              <template #prefix>
                <LucideMapPin class="size-4 mr-1.5" />
              </template>
            </Link>
          </div>

          <FormControl
            class="[&_p]:text-p-xs"
            type="text"
            :label="__('Domain')"
            placeholder="frappe.io"
            v-model="state.domain"
          >
            <template #prefix>
              <LucideGlobe class="size-4" />
            </template>
          </FormControl>
        </div>

        <hr class="my-5 border-outline-gray-2" />

        <div class="flex flex-col gap-3">
          <h3 class="text-base-medium text-ink-gray-8">
            {{ __("Primary Contact") }}
          </h3>
          <FormControl
            class="[&_p]:text-p-xs"
            type="email"
            :label="__('Email')"
            placeholder="name@company.com"
            v-model="primaryContact.email"
          >
            <template #prefix>
              <LucideMail class="size-4" />
            </template>
          </FormControl>
          <div
            class="overflow-hidden transition-[height] duration-200 ease-in-out"
            :style="{ height: contactSwapHeight }"
          >
            <div ref="contactSwapEl" class="flex flex-col gap-3">
              <div
                v-if="existingContact"
                class="flex items-center gap-3 rounded-lg border border-outline-gray-2 p-3"
              >
                <Avatar
                  size="xl"
                  shape="circle"
                  :label="existingContactName"
                  :image="existingContact.image"
                />
                <div class="flex min-w-0 flex-col gap-0.5">
                  <span class="truncate text-p-sm text-ink-gray-8">
                    {{ existingContactName }}
                  </span>
                  <span class="truncate text-p-xs text-ink-gray-5">
                    {{ existingContactDetail }}
                  </span>
                </div>
                <div class="ml-auto flex shrink-0 items-center gap-1">
                  <Button
                    variant="ghost"
                    :aria-label="__('Open contact in new tab')"
                    @click="openContact"
                  >
                    <template #icon>
                      <LucideExternalLink class="size-4" />
                    </template>
                  </Button>
                  <Button
                    variant="ghost"
                    :aria-label="__('Dismiss')"
                    @click="dismissExistingContact"
                  >
                    <template #icon>
                      <LucideX class="size-4" />
                    </template>
                  </Button>
                </div>
              </div>
              <template v-else>
                <div class="grid grid-cols-2 gap-4">
                  <FormControl
                    class="[&_p]:text-p-xs"
                    type="text"
                    :label="__('First Name')"
                    placeholder="John"
                    v-model="primaryContact.firstName"
                  />
                  <FormControl
                    class="[&_p]:text-p-xs"
                    type="text"
                    :label="__('Last Name')"
                    placeholder="Doe"
                    v-model="primaryContact.lastName"
                  />
                </div>
                <PhoneControl
                  :label="__('Mobile Number')"
                  v-model="primaryContact.mobileNo"
                />
                <div
                  v-if="primaryContact.email"
                  class="flex items-center gap-2 text-p-xs text-ink-gray-5"
                >
                  <LucideInfo class="size-3.5 shrink-0" />
                  <span>{{
                    __("An invitation will be sent to this email")
                  }}</span>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </template>

    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          :label="__('Create')"
          theme="gray"
          variant="solid"
          :loading="customerResource.loading"
          @click.prevent="addCustomer"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import ImageAvatar from "@/components/ImageAvatar.vue";
import {
  customerTypeOptions,
  useNewCustomerForm,
} from "@/composables/customer";
import { __ } from "@/translation";
import type { Resource } from "@/types";
import { getErrorMessage, validateEmailWithZod } from "@/utils";
import { useElementSize } from "@vueuse/core";
import {
  Avatar,
  Button,
  Dialog,
  FormControl,
  createResource,
  toast,
} from "frappe-ui";
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import LucideExternalLink from "~icons/lucide/external-link";
import LucideGlobe from "~icons/lucide/globe";
import LucideInfo from "~icons/lucide/info";
import LucideMail from "~icons/lucide/mail";
import LucideMapPin from "~icons/lucide/map-pin";
import LucideX from "~icons/lucide/x";
import Link from "../frappe-ui/Link.vue";
import PhoneControl from "../frappe-ui/PhoneControl/PhoneControl.vue";

const model = defineModel<boolean>({ default: false });
const router = useRouter();

const {
  state,
  primaryContact,
  existingContact,
  existingContactName,
  dismissExistingContact,
  reset,
} = useNewCustomerForm();

const contactSwapEl = ref<HTMLElement | null>(null);
const { height: contactSwapContentHeight } = useElementSize(contactSwapEl);
const contactSwapHeight = computed(() =>
  contactSwapContentHeight.value
    ? `${contactSwapContentHeight.value}px`
    : "auto"
);

const existingContactDetail = computed(() => {
  const contact = existingContact.value;
  const mobile = contact?.mobile_no || contact?.phone;
  const note = contact?.user
    ? __("Will be added as the primary contact")
    : __("Will be set as primary · an invitation will be sent");
  return mobile ? `${mobile} · ${note}` : note;
});

function openContact() {
  if (!existingContact.value) return;
  const route = router.resolve({
    name: "Contact",
    params: { id: existingContact.value.name },
  });
  window.open(route.href, "_blank");
}

const customerResource: Resource = createResource({
  url: "helpdesk.api.customer.create_customer",
  method: "POST",
  onSuccess: (data: { name: string; invited_emails: string[] }) => {
    router.push({ name: "Customer", params: { id: data.name } });
    const invited = data.invited_emails?.[0];
    toast.success(
      invited
        ? __("Customer created · invitation sent to {0}", invited)
        : __("Customer created")
    );
  },
  onError: (error: unknown) => {
    getErrorMessage(error, true);
  },
});

function addCustomer() {
  if (!state.name) {
    toast.error(__("Name is required"));
    return;
  }
  if (!validatePrimaryContact()) return;

  customerResource.submit({
    customer: {
      customer_name: state.name,
      customer_type: state.customerType,
      domain: state.domain,
      image: state.image,
      country: state.country,
    },
    primary_contact: buildPrimaryContactPayload(),
  });
}

function buildPrimaryContactPayload(): Record<string, string> | null {
  if (existingContact.value) return { email: primaryContact.email };
  if (!hasPrimaryContactData()) return null;
  return {
    first_name: primaryContact.firstName,
    last_name: primaryContact.lastName,
    email: primaryContact.email,
    mobile_no: primaryContact.mobileNo,
  };
}

function validatePrimaryContact(): boolean {
  if (existingContact.value) return true;
  if (!hasPrimaryContactData()) return true;
  if (!primaryContact.firstName) {
    toast.error(__("Enter the primary contact's first name"));
    return false;
  }
  if (!primaryContact.email) {
    toast.error(__("Enter the primary contact's email"));
    return false;
  }
  if (!validateEmailWithZod(primaryContact.email)) {
    toast.error(__("Invalid email address"));
    return false;
  }
  return true;
}

function hasPrimaryContactData(): boolean {
  return Boolean(
    primaryContact.firstName ||
      primaryContact.lastName ||
      primaryContact.email ||
      primaryContact.mobileNo
  );
}
</script>
