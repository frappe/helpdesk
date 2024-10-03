<template>
  <div class="flex flex-col overflow-y-auto">
    <TicketBreadcrumbs
      :parent="route.meta.parent"
      title="New"
      :current="route.name"
    />
    <!-- Container -->
    <div class="max-w-screen-xl mx-5 flex flex-col gap-5 mb-5">
      <div v-if="Boolean(template.data?.about)" class="mx-5 my-3">
        {{ template.data.about }}
        <div class="prose-f" v-html="sanitize(template.data.about)" />
      </div>
      <div
        class="grid grid-cols-1 gap-4 sm:grid-cols-3"
        v-if="Boolean(visibleFields)"
      >
        <UniInput
          v-for="field in visibleFields"
          :key="field.fieldname"
          :field="field"
          :value="templateFields[field.fieldname]"
          @change="templateFields[field.fieldname] = $event.value"
        />
      </div>
      <div>
        <FormControl
          v-model="subject"
          type="text"
          label="Subject*"
          placeholder="A short description"
        />
      </div>
      <TicketNewArticles v-if="isCustomerPortal" :search="subject" />
      <div v-if="isCustomerPortal">
        <TicketTextEditor
          v-show="subject.length > 2 || description.length > 0"
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
                $refs.editor.editor.isEmpty || ticket.loading || !subject
              "
              @click="() => ticket.submit()"
            />
          </template>
        </TicketTextEditor>
        <h4
          v-show="subject.length <= 2 && description.length === 0"
          class="text-lg text-gray-500"
        >
          Please enter a subject to continue
        </h4>
      </div>

      <!-- for agent portal -->
      <div v-else>
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
                $refs.editor.editor.isEmpty || ticket.loading || !subject
              "
              @click="() => ticket.submit()"
            />
          </template>
        </TicketTextEditor>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { createResource, usePageMeta, Button, FormControl } from "frappe-ui";
import sanitizeHtml from "sanitize-html";
import { isEmpty } from "lodash";
import { useError } from "@/composables/error";
import { UniInput } from "@/components";
import TicketBreadcrumbs from "./ticket/TicketBreadcrumbs.vue";
import TicketNewArticles from "./ticket/TicketNewArticles.vue";
import TicketTextEditor from "./ticket/TicketTextEditor.vue";
import { useAuthStore } from "@/stores/auth";
import { capture } from "@/telemetry";

interface P {
  templateId?: string;
}

const props = withDefaults(defineProps<P>(), {
  templateId: "",
});

const route = useRoute();
const router = useRouter();
const subject = ref("");
const description = ref("");
const attachments = ref([]);
const templateFields = reactive({});

const isCustomerPortal = window.location.pathname.includes("/my-tickets");

const template = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket_template.api.get_one",
  makeParams: () => ({
    name: props.templateId || "Default",
  }),
  auto: true,
});

const visibleFields = computed(() =>
  template.data?.fields?.filter(
    (f) => route.meta.agent || !f.hide_from_customer
  )
);
const ticket = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket.api.new",
  debounce: 300,
  makeParams: () => ({
    doc: {
      description: description.value,
      subject: subject.value,
      template: props.templateId,
      ...templateFields,
    },
    attachments: attachments.value,
  }),
  validate: (params) => {
    const fields = visibleFields.value?.filter((f) => f.required) || [];
    const toVerify = [...fields, "subject", "description"];
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
    if (!isCustomerPortal) return;
    // only capture telemetry for customer portal
    capture("new_ticket_submitted", {
      data: {
        user: userID,
        ticketID: data.name,
        subject: subject.value,
        description: description.value,
        customFields: templateFields,
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

usePageMeta(() => ({
  title: "New Ticket",
}));

const { userId: userID } = useAuthStore();
onMounted(() => {
  capture("new_ticket_page", {
    data: {
      user: userID,
    },
  });
});
</script>
