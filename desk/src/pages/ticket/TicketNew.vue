<template>
  <div class="flex flex-col overflow-y-auto">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" />
      </template>
    </LayoutHeader>
    <!-- Container -->
    <div
      class="flex flex-col gap-5 py-6 h-full flex-1 self-center overflow-auto mx-auto w-full max-w-4xl px-5"
    >
      <!-- custom fields descriptions -->
      <div v-if="Boolean(template.data?.about)" class="">
        <div class="prose-f" v-html="sanitize(template.data.about)" />
      </div>
      <!-- custom fields -->
      <div
        class="grid grid-cols-1 gap-4 sm:grid-cols-3"
        v-if="Boolean(visibleFields)"
      >
        <UniInput
          v-for="field in visibleFields"
          :key="field.fieldname"
          :field="field"
          :value="templateFields[field.fieldname]"
          @change="
            (e) => {
              templateFields[field.fieldname] = e.value;
              const fn = customOnChange[field.fieldname];
              if (fn) fn(e.value, field.fieldtype);
            }
          "
        />
      </div>
      <!-- existing fields -->
      <div class="flex flex-col" :class="subject.length >= 2 && 'gap-5'">
        <div class="flex flex-col gap-2">
          <span class="block text-sm text-gray-700">
            Subject
            <span class="place-self-center text-red-500"> * </span>
          </span>
          <FormControl
            v-model="subject"
            type="text"
            placeholder="A short description"
          />
        </div>
        <SearchArticles
          v-if="isCustomerPortal"
          :query="subject"
          class="shadow"
        />
        <div v-if="isCustomerPortal">
          <h4
            v-show="subject.length <= 2 && description.length === 0"
            class="text-p-sm text-gray-500 ml-1"
          >
            Please enter a subject to continue
          </h4>
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
        </div>
      </div>

      <!-- for agent portal -->
      <div v-if="!isCustomerPortal">
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
import {
  createResource,
  usePageMeta,
  Button,
  FormControl,
  Breadcrumbs,
} from "frappe-ui";
import sanitizeHtml from "sanitize-html";
import { isEmpty } from "lodash";
import { setupCustomizations } from "@/utils";
import { LayoutHeader, UniInput } from "@/components";
import SearchArticles from "../../components/SearchArticles.vue";
import TicketTextEditor from "./TicketTextEditor.vue";
import { useAuthStore } from "@/stores/auth";
import { capture } from "@/telemetry";
import { isCustomerPortal } from "@/utils";

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

const template = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket_template.api.get_one",
  makeParams: () => ({
    name: props.templateId || "Default",
  }),
  auto: true,
  transform: (data) => {
    setupCustomizations(data, {
      doc: data,
      updateOptions,
    });
  },
  onSuccess: (data) => {
    oldFields = window.structuredClone(data.fields || []);
  },
});

let oldFields = [];

function updateOptions(fieldname: string, newOptions: any) {
  const f = template.data.fields.find((f) => f.fieldname === fieldname);
  if (!f) return;
  if (!newOptions) {
    f.options = oldFields.find((f) => f.fieldname === fieldname).options;
    return;
  }
  f.options = newOptions.join("\n");
}

const customOnChange = computed(() => template.data?._customOnChange);

const visibleFields = computed(() => {
  let _fields = template.data?.fields?.filter(
    (f) => route.meta.agent || !f.hide_from_customer
  );
  if (!_fields) return [];
  return _fields.map((field) => parseField(field));
});

function parseField(field) {
  return {
    display_via_depends_on: evaluateDependsOnValue(field?.depends_on),
    ...field,
    required:
      field.required ||
      (field.mandatory_depends_on &&
        evaluateDependsOnValue(field.mandatory_depends_on)),
  };
}

function evaluateDependsOnValue(expression) {
  if (!expression) return true;
  let out = null;

  if (expression.substr(0, 5) == "eval:") {
    try {
      out = _eval(expression.substr(5), { doc: templateFields });
    } catch (e) {
      out = true;
    }
  } else {
    out = false;
  }
  return out;
}
function _eval(code, context = {}) {
  let variable_names = Object.keys(context);
  let variables = Object.values(context);
  code = `let out = ${code}; return out`;
  try {
    let expression_function = new Function(...variable_names, code);
    return expression_function(...variables);
  } catch (error) {
    console.log("Error evaluating the following expression:");
    console.error(code);
    throw error;
  }
}

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
      name: isCustomerPortal.value ? "TicketCustomer" : "TicketAgent",
      params: {
        ticketId: data.name,
      },
    });
    if (!isCustomerPortal.value) return;
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
});

function sanitize(html: string) {
  return sanitizeHtml(html, {
    allowedTags: sanitizeHtml.defaults.allowedTags.concat(["img"]),
  });
}

const breadcrumbs = computed(() => {
  const items = [
    {
      label: "Tickets",
      route: {
        name: "TicketsCustomer",
      },
    },
    {
      label: "New Ticket",
      route: {
        name: "TicketNew",
      },
    },
  ];
  return items;
});

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
