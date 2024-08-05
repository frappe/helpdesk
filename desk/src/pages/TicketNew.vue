<template>
  <div class="flex flex-col overflow-y-auto">
    <TicketBreadcrumbs
      :parent="route.meta.parent"
      title="New"
      :current="route.name"
    />
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
              $refs.editor.editor.isEmpty || ticket.loading || !subject
            "
            @click="() => ticket.submit()"
          />
        </template>
      </TicketTextEditor>
    </span>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { createResource, usePageMeta, Button, FormControl } from "frappe-ui";
import sanitizeHtml from "sanitize-html";
import { isEmpty } from "lodash";
import { useError } from "@/composables/error";
import { UniInput } from "@/components";
import TicketBreadcrumbs from "./ticket/TicketBreadcrumbs.vue";
import TicketNewArticles from "./ticket/TicketNewArticles.vue";
import TicketTextEditor from "./ticket/TicketTextEditor.vue";
import { capture, recordSession, stopSession } from "@/telemetry";
interface P {
  templateId?: string;
}

const props = withDefaults(defineProps<P>(), {
  templateId: "",
});

onMounted(() => {
  capture("new_ticket_page");
  recordSession();
});

onUnmounted(() => {
  stopSession();
});

const route = useRoute();
const router = useRouter();
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
</script>
