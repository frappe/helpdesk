<template>
  <Dialog v-model:open="open" size="md" bare :dismissible="!isDirty">
    <template #default>
      <div class="bg-surface-modal px-4 py-5 sm:px-6">
        <div class="mb-6 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __("Edit Contact") }}
            </h3>
            <Badge
              v-if="isDirty"
              :label="__('Unsaved')"
              variant="subtle"
              theme="orange"
            />
          </div>
          <Button icon="x" variant="ghost" @click="open = false" />
        </div>

        <div class="space-y-4">
          <!-- Avatar -->
          <ImageAvatar
            v-model="state.image"
            :label="__('Photo')"
            :fallback-label="
              `${state.firstName} ${state.lastName}`.trim() || __('Contact')
            "
            shape="circle"
          />

          <!-- First + Last name -->
          <div class="grid grid-cols-2 gap-4">
            <FormControl
              class="[&_p]:text-p-xs"
              :label="__('First Name')"
              type="text"
              :required="true"
              :placeholder="__('John')"
              v-model="state.firstName"
            />
            <FormControl
              class="[&_p]:text-p-xs"
              :label="__('Last Name')"
              type="text"
              :placeholder="__('Doe')"
              v-model="state.lastName"
            />
          </div>
          <!-- Email IDs -->
          <div class="space-y-1.5">
            <label class="block text-p-sm font-medium text-ink-gray-7">
              {{ __("Email") }}
              <span class="text-ink-red-3">*</span>
            </label>
            <ContactInputRow
              v-for="(email, index) in state.emails"
              :key="email.key"
              v-model="email.email_id"
              type="email"
              placeholder="name@example.com"
              :isPrimary="email.isPrimary"
              :canRemove="!email.isPrimary"
              :autofocus="email.key === autofocusKey"
              @setPrimary="setPrimary('email', index)"
              @remove="removeRow('email', index)"
            />
            <Button
              key="add-email"
              size="sm"
              :label="__('Add Email')"
              @click="addRow('email')"
            >
              <template #prefix>
                <LucidePlus class="size-3.5" />
              </template>
            </Button>
          </div>

          <!-- Phone numbers -->
          <div class="space-y-1.5 flex flex-col items-start w-full flex-1">
            <label class="block text-p-sm font-medium text-ink-gray-7">{{
              __("Phone")
            }}</label>
            <ContactInputRow
              v-for="(phone, index) in state.phones"
              :key="phone.key"
              v-model="phone.phone"
              type="tel"
              :isPrimary="phone.isPrimary"
              :canRemove="true"
              :canTogglePrimary="true"
              :autofocus="phone.key === autofocusKey"
              @setPrimary="setPrimary('phone', index)"
              @remove="removeRow('phone', index)"
            />
            <Button
              key="add-phone"
              size="sm"
              :label="__('Add Phone')"
              @click="addRow('phone')"
            >
              <template #prefix>
                <LucidePlus class="size-3.5" />
              </template>
            </Button>
          </div>

          <!-- Timezone -->
          <div v-if="doc.doc?.user" class="space-y-1.5">
            <label class="block text-p-sm font-medium text-ink-gray-7">{{
              __("Timezone")
            }}</label>
            <TimezoneControl v-model="state.timezone" />
          </div>

          <!-- Customer -->
          <div class="space-y-1.5">
            <label
              class="block text-p-sm font-medium text-ink-gray-7"
              v-if="!contactInfoResource.data?.invitation"
            >
              {{ __("Customer") }}
            </label>

            <!-- Already linked: read-only, opens the customer in a new tab -->
            <div
              v-for="customer in linkedCustomers"
              :key="customer.name"
              class="flex items-center gap-2"
            >
              <FormControl
                class="flex-1"
                type="text"
                :modelValue="customer.name"
                readonly
              >
                <template #prefix>
                  <Avatar
                    :label="customer.name"
                    :image="customer.image"
                    size="sm"
                  />
                </template>
              </FormControl>
              <Button
                variant="ghost"
                :tooltip="__('Open customer')"
                @click="goToCustomer(customer.name)"
              >
                <template #icon>
                  <LucideExternalLink class="size-4 text-ink-gray-5" />
                </template>
              </Button>
            </div>

            <!-- Link a customer (only while none is linked yet) -->
            <Link
              v-if="canLinkCustomer"
              v-model="state.customer"
              doctype="HD Customer"
              :placeholder="__('Select Customer')"
            />
          </div>

          <!-- Save -->
          <div class="flex justify-end">
            <Button
              :label="__('Save')"
              variant="solid"
              theme="gray"
              :disabled="!isDirty"
              :loading="
                editContactResource.loading || linkCustomerResource.loading
              "
              @click="handleSave"
            />
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import Link from "@/components/frappe-ui/Link.vue";
import ImageAvatar from "@/components/ImageAvatar.vue";
import { nextEntryKey, useContact } from "@/composables/contact";
import { __ } from "@/translation";
import type { Error } from "@/types";
import { getErrorMessage } from "@/utils";
import { Avatar, Badge, Button, Dialog, FormControl } from "frappe-ui";
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import LucideExternalLink from "~icons/lucide/external-link";
import LucidePlus from "~icons/lucide/plus";
import TimezoneControl from "../TimezoneControl.vue";
import ContactInputRow from "./ContactInputRow.vue";

const props = defineProps<{ name: string }>();
const open = defineModel<boolean>({ default: false });

const {
  state,
  parseContactData,
  isDirty,
  isContactDirty,
  editContactResource,
  linkCustomerResource,
  doc,
  contactInfoResource,
} = useContact(props.name);

const router = useRouter();
const autofocusKey = ref<number | null>(null);

const linkedCustomers = computed<{ name: string; image?: string | null }[]>(
  () => contactInfoResource.data?.customers ?? []
);
const canLinkCustomer = computed(
  () =>
    linkedCustomers.value.length === 0 && !contactInfoResource.data?.invitation
);

function goToCustomer(name: string) {
  const route = router.resolve({ name: "Customer", params: { id: name } });
  window.open(route.href, "_blank");
}

function addRow(type: "email" | "phone") {
  const key = nextEntryKey();
  if (type === "email") {
    state.emails.push({
      email_id: "",
      isPrimary: state.emails.length === 0,
      key,
    });
  } else {
    state.phones.push({
      phone: "",
      isPrimary: false,
      key,
    });
  }
  autofocusKey.value = key;
}

function removeRow(type: "email" | "phone", index: number) {
  const list = type === "email" ? state.emails : state.phones;
  const wasPrimary = list[index]?.isPrimary;
  list.splice(index, 1);
  if (type === "email") {
    const first = list[0];
    if (wasPrimary && first) {
      first.isPrimary = true;
    }
  }
}

function setPrimary(type: "email" | "phone", index: number) {
  if (type === "email") {
    state.emails.forEach((e, i) => {
      e.isPrimary = i === index;
    });
  } else {
    const wasPrimary = Boolean(state.phones[index]?.isPrimary);
    state.phones.forEach((p, i) => {
      p.isPrimary = i === index ? !wasPrimary : false;
    });
  }
}

async function handleSave() {
  const tasks: Promise<unknown>[] = [];
  if (isContactDirty.value) {
    tasks.push(
      editContactResource.submit({ name: props.name, doc: parseContactData() })
    );
  }
  if (state.customer) {
    tasks.push(linkCustomerResource.submit());
  }
  if (!tasks.length) return;
  try {
    await Promise.all(tasks);
    state.customer = "";
    open.value = false;
    doc.reload();
    contactInfoResource.reload();
  } catch (error) {
    getErrorMessage(error as Error, true);
  }
}
</script>

<style scoped>
.row-leave-active {
  position: absolute;
  width: 100%;
  transition: opacity 180ms cubic-bezier(0.2, 0, 0, 1),
    transform 180ms cubic-bezier(0.2, 0, 0, 1);
}
.row-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
