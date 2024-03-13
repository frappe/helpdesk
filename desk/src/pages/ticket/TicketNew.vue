<template>
  <div class="flex flex-col">
    <TicketBreadcrumbs :parent="route.meta.parent" title="New" />
    <div v-if="template.data?.about" class="mx-5 my-3">
      <div class="prose-f" v-html="sanitize(template.data.about)" />
    </div>
    <div class="grid grid-cols-1 gap-4 px-5 sm:grid-cols-3">
      <UniInput
        v-for="field in visibleFields"
        :key="field.fieldname"
        :field="field"
        :value="templateFields[field.fieldname]"
        @change="templateFields[field.fieldname] = $event.value"
      />
    </div>
    <div class="m-5">
      <div class="space-y-1.5">
        <div>
          <span class="block text-xs text-gray-600">
            Customer
          </span>
        </div>
        <Autocomplete
          :value="selectedCustomer"
          :resource-options="{
            url: 'helpdesk.extends.client.get_list',
            inputMap: (query) => ({
              doctype: 'HD Customer',
              pluck: 'name',
              filters: [['name', 'like', `%${query}%`]]
            }),
            responseMap: (res) => res.map(d => ({ label: d.name, value: d.name }))
          }"
          @change="handleCustomerChange"
          placeholder="Search for a customer"
        />
        <!-- Display validation error if it exists -->
        <p v-if="customerValidationError" class="whitespace-pre-line text-sm text-red-600" role="alert">{{ customerValidationError }}</p>
      </div>
    </div>
    <div class="mx-5 mb-5" v-if="selectedCustomer">
      <div class="space-y-1.5">
        <div>
          <span class="block text-xs text-gray-600">
            Contact
          </span>
        </div>
        <Autocomplete
          :value="selectedContact"
          :resource-options="{
            url: 'frappe.client.get_list',
            inputMap: (query) => ({
              doctype: 'Contact',
              fields: ['name', 'full_name'],
              filters: [['Dynamic Link', 'link_doctype', '=', 'HD Customer'], ['Dynamic Link', 'link_title', '=', selectedCustomer ]],
              limit_page_length: 999,
            }),
            responseMap: (res) => res.map(d => ({ label: d.full_name, value: d.name }))
          }"
          @change="handleContactChange"
          placeholder="Search for a contact"
        />
        <!-- Display validation error if it exists -->
        <p v-if="contactValidationError" class="whitespace-pre-line text-sm text-red-600" role="alert">{{ contactValidationError }}</p>
      </div>
    </div>
    <div class="mx-5 mb-5">
      <FormControl
        v-model="subject"
        type="text"
        label="Subject"
        placeholder="A short description"
      />
    </div>
    <TicketNewArticles :search="subject" class="mx-5 mb-5" />
    <span class="mx-5 mb-5">
      <TicketTextEditor
        ref="editor"
        v-model:attachments="attachments"
        v-model:content="description"
        placeholder="Detailed explanation"
        expand
      >
        <template #bottom-right>
          <Button
            label="Submit"
            theme="gray"
            variant="solid"
            :disabled="
              $refs.editor.editor.isEmpty || ticket.loading || !subject || !selectedCustomer || !selectedContact
            "
            @click="() => ticket.submit()"
          />
        </template>
      </TicketTextEditor>
    </span>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from "vue";
import { useRoute, useRouter } from "vue-router";
import { createResource, usePageMeta, Button, FormControl } from "frappe-ui";
import sanitizeHtml from "sanitize-html";
import { isEmpty } from "lodash";
import { useError } from "@/composables/error";
import { UniInput } from "@/components";
import TicketBreadcrumbs from "./TicketBreadcrumbs.vue";
import TicketNewArticles from "./TicketNewArticles.vue";
import TicketTextEditor from "./TicketTextEditor.vue";
import Autocomplete from "@/components/global/Autocomplete.vue";

interface P {
  templateId?: string;
}

const props = withDefaults(defineProps<P>(), {
  templateId: "",
});

const route = useRoute();
const router = useRouter();
const selectedCustomer = ref("");
const customerValidationError = ref("");
const selectedContact = ref("");
const contactValidationError = ref("");
const subject = ref("");
const description = ref("");
const attachments = ref([]);
const templateFields = reactive({});

const template = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket_template.api.get_one",
  makeParams: () => ({
    name: props.templateId || "Default",
  }),
  auto: true,
});

const visibleFields = computed(() =>
  template.data?.fields.filter((f) => route.meta.agent || !f.hide_from_customer)
);
const ticket = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket.api.new",
  debounce: 300,
  makeParams: () => ({
    doc: {
      customer: selectedCustomer.value,
      contact: selectedContact.value,
      description: description.value,
      subject: subject.value,
      template: props.templateId,
      ...templateFields,
    },
    attachments: attachments.value,
  }),
  validate: (params) => {
    const fields = visibleFields.value.filter((f) => f.required);
    const toVerify = [...fields, "subject", "description"];
    if (!selectedCustomer.value) {
      customerValidationError.value = "Selecting a customer is required.";
      return "Selecting a customer is required.";
    } else {
      customerValidationError.value = "";
    }
    if (!selectedContact.value) {
      contactValidationError.value = "Selecting a contact is required.";
      return "Selecting a contact is required.";
    } else {
      contactValidationError.value = "";
    }
    for (const field of toVerify) {
      if (isEmpty(params.doc[field.fieldname || field])) {
        return `${field.label || field} is required`;
      }
    }
  },
  onSuccess: (data) => {
    router.push({
      name: route.meta.onSuccessRoute as string,
      params: {
        ticketId: data.name,
      },
    });
  },
  onError: useError(),
});

function sanitize(html: string) {
  return sanitizeHtml(html, {
    allowedTags: sanitizeHtml.defaults.allowedTags.concat(["img"]),
  });
}

function handleCustomerChange(item) {
  selectedCustomer.value = item ? item.value : "";
  selectedContact.value = "";
  validateCustomerSelection();
}

function validateCustomerSelection() {
  customerValidationError.value = "";

  if (!selectedCustomer.value) {
    customerValidationError.value = "Customer selection is required.";
    return false;
  }
  return true;
}

function handleContactChange(item) {
  selectedContact.value = item ? item.value : "";
  validateContactSelection();
}

function validateContactSelection() {
  contactValidationError.value = "";
  if (!selectedContact.value) {
    contactValidationError.value = "Contact selection is required.";
    return false;
  }
  return true;
}

usePageMeta(() => ({
  title: "New Ticket",
}));
</script>
