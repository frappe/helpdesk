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
    <TicketNewArticles :search="subject" class="mx-5 mb-5" />
    <span class="mx-5 mb-5">
      <TicketTextEditor
        ref="editor"
        v-model:attachments="attachments"
        v-model:content="description"
        placeholder="Detailed explanation"
        expand
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
            <TabButtons
              v-model="mode"
              :buttons="Object.values(Mode).map((m) => ({ label: m }))"
            />
          </span>
        </template>
        <template v-if="mode == Mode.Response" #top-bottom>
          <div class="my-3 flex flex-col gap-y-1">
            <span class="inline-flex flex-wrap items-center gap-1">
              <span class="mr-2 text-xs text-gray-500">TO:</span>
              <FormControl
                v-model="email_id"
                type="email"
                placeholder="hello@example.com"
                class="w-1/6"
              />
            </span>
            <span class="inline-flex flex-wrap items-center gap-1">
              <span v-if="showCc" class="mr-2 text-xs text-gray-500">CC:</span>
              <FormControl
                v-if="showCc"
                v-model="cc"
                type="email"
                placeholder="hello@example.com"
                class="w-1/6"
              />
            </span>
            <span class="inline-flex flex-wrap items-center gap-1">
              <span v-if="showBcc" class="mr-2 text-xs text-gray-500"
                >BCC:</span
              >
              <FormControl
                v-if="showBcc"
                v-model="bcc"
                type="email"
                placeholder="hello@example.com"
                class="w-1/6"
              />
            </span>

            <div class="mt-3">
              <FormControl
                v-model="subject"
                type="text"
                label="Subject"
                placeholder="A short description"
              />
            </div>
          </div>
        </template>
        <template v-else #top-bottom>
          <div class="my-3 flex flex-col gap-y-3">
            <FormControl
              v-model="subject"
              type="text"
              label="Subject"
              placeholder="A short description"
            />
          </div>
        </template>
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
import { ref, computed, reactive } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  createResource,
  usePageMeta,
  Button,
  FormControl,
  TabButtons,
} from "frappe-ui";
import sanitizeHtml from "sanitize-html";
import { isEmpty } from "lodash";
import { useError } from "@/composables/error";
import { UniInput } from "@/components";
import TicketBreadcrumbs from "./TicketBreadcrumbs.vue";
import TicketNewArticles from "./TicketNewArticles.vue";
import TicketTextEditor from "./TicketTextEditor.vue";

interface P {
  templateId?: string;
}

enum Mode {
  Comment = "Comment",
  Response = "Response",
}

const props = withDefaults(defineProps<P>(), {
  templateId: "",
});
const route = useRoute();
const router = useRouter();
const subject = ref("");
const email_id = ref("");
const cc = ref("");
const bcc = ref("");
const description = ref("");
const attachments = ref([]);
const templateFields = reactive({});
const showCc = ref(false);
const showBcc = ref(false);
const mode = ref(Mode.Comment);

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
      description: description.value,
      subject: subject.value,
      template: props.templateId,
      ...templateFields,
    },
    attachments: attachments.value,
    email_id: email_id.value,
    cc: cc.value,
    bcc: bcc.value,
  }),
  validate: (params) => {
    const fields = visibleFields.value.filter((f) => f.required);
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
