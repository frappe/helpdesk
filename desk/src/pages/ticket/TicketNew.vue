<template>
  <div class="flex flex-col overflow-y-auto">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" />
      </template>
      <template #right-header>
        <CustomActions
          v-if="template.data?._customActions"
          :actions="template.data?._customActions"
        />
      </template>
    </LayoutHeader>

    <div
      class="flex flex-col gap-5 py-6 h-full flex-1 self-center overflow-auto mx-auto w-full max-w-4xl px-5"
    >
      <!-- custom fields descriptions -->
      <div v-if="Boolean(template.data?.about)">
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
            (e) => handleOnFieldChange(e, field.fieldname, field.fieldtype)
          "
        />
      </div>

      <!-- Project + Subject + Description -->
      <div
        class="flex flex-col"
        :class="(subject.length >= 2 || description.length) && 'gap-5'"
      >
        <!-- PROJECT FIELD -->
        <div class="flex flex-col gap-2">
          <span class="block text-sm text-gray-700">
            {{ __("Project") }}
            <span class="text-red-500">*</span>
          </span>

          <FormControl
            v-model="custom_project"
            type="select"
           :options="projectOptions"
            :placeholder="__('Select project')"
          />
        </div>

        <!-- SUBJECT FIELD -->
        <div class="flex flex-col gap-2">
          <span class="block text-sm text-gray-700">
            {{ __("Subject") }}
            <span class="text-red-500">*</span>
          </span>
          <FormControl
            v-model="subject"
            type="text"
            :placeholder="__('A short description')"
          />
        </div>

        <!-- DESCRIPTION -->
        <TicketTextEditor
          ref="editor"
          v-model:attachments="attachments"
          v-model:content="description"
          :placeholder="__('Detailed explanation')"
          expand
        >
          <template #bottom-right>
            <Button
              :label="__('Submit')"
              theme="gray"
              variant="solid"
              :disabled="
                $refs.editor?.editor?.isEmpty ||
                ticket.loading ||
                !subject ||
                !custom_project
              "
              @click="ticket.submit()"
            />
          </template>
        </TicketTextEditor>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { LayoutHeader, UniInput } from "@/components";
import { useAuthStore } from "@/stores/auth";
import { globalStore } from "@/stores/globalStore";
import { capture } from "@/telemetry";
import {
  Breadcrumbs,
  Button,
  createResource,
  FormControl,
  usePageMeta,
} from "frappe-ui";
import { __ } from "@/translation";
import sanitizeHtml from "sanitize-html";
import { computed, defineAsyncComponent, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";

const TicketTextEditor = defineAsyncComponent(
  () => import("./TicketTextEditor.vue")
);

interface P {
  templateId?: string;
}

const props = withDefaults(defineProps<P>(), {
  templateId: "",
});

const router = useRouter();
const { userId } = useAuthStore();

const subject = ref("");
const description = ref("");
const custom_project = ref("");
const attachments = ref([]);
const templateFields = reactive({});

/* ---------------- TEMPLATE RESOURCE ---------------- */

const template = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket_template.api.get_one",
  makeParams: () => ({
    name: props.templateId || "Default",
  }),
  auto: true,
});

/* ---------------- FILTER PROJECT BY USER ---------------- */


const projectResource = createResource({
  url: "helpdesk.api.project_api.get_user_projects",
  makeParams: () => ({
    doctype: "Project",
    txt: "",
    searchfield: "name",
    start: 0,
    page_len: 100,
  }),
  auto: true,
});
console.log("projectResource", projectResource);
const projectOptions = computed(() => {
  if (!projectResource.data) return [];

  // Frappe SQL returns list of arrays like: [["PROJ-001"], ["PROJ-002"]]
  return projectResource.data.map((p: any) => {
    // If array format
    if (Array.isArray(p)) {
      return {
         value: p[0], // Project ID (name)
        label: `${p[0]} - ${p[1]}`, // ID + Project Name
        }
    }
    // If object format
    return p.name;
  });
});
console.log("projectOptions", projectOptions);


/* ---------------- TICKET CREATION ---------------- */

const ticket = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket.api.new",
  debounce: 300,
  makeParams: () => ({
    doc: {
      subject: subject.value,
      description: description.value,
      custom_project: custom_project.value,
      template: props.templateId,
      ...templateFields,
    },
    attachments: attachments.value,
  }),
  validate: (params) => {
    if (!params.doc.custom_project) return "Project is required";
    if (!params.doc.subject) return "Subject is required";
    if (!params.doc.description) return "Description is required";
  },
  onSuccess: (data) => {
    router.push({
      name: "TicketAgent",
      params: {
        ticketId: data.name,
      },
    });

    capture("new_ticket_submitted", {
      data: {
        user: userId,
        ticketID: data.name,
        subject: subject.value,
        project: custom_project.value,
      },
    });
  },
});

/* ---------------- UTILITIES ---------------- */

function sanitize(html: string) {
  return sanitizeHtml(html, {
    allowedTags: sanitizeHtml.defaults.allowedTags.concat(["img"]),
  });
}

const breadcrumbs = computed(() => [
  { label: __("Tickets"), route: { name: "TicketsAgent" } },
  { label: __("New Ticket"), route: { name: "TicketNew" } },
]);

usePageMeta(() => ({
  title: __("New Ticket"),
}));

onMounted(() => {
  capture("new_ticket_page", {
    data: { user: userId },
  });
});
</script>
