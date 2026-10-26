<template>
  <div
    v-if="template.data || template.error"
    class="portal-reveal flex w-full flex-col"
  >
    <div class="flex w-full flex-col gap-5">
      <div
        v-if="template.data?.about"
        class="prose prose-sm max-w-none text-ink-gray-7"
        v-html="about"
      />
      <div class="flex w-full flex-col gap-2">
        <FormControl
          v-model="subject"
          class="w-full"
          type="text"
          size="sm"
          variant="subtle"
          maxlength="140"
          required
          :label="__('Subject')"
          :placeholder="__('A short description')"
        />
        <PortalRelatedArticles
          v-if="suggestArticles"
          :articles="suggestions.data"
        />
      </div>
      <div class="flex w-full flex-col">
        <span class="mb-1.5 block text-p-sm text-ink-gray-5">
          {{ __("Description") }}
        </span>
        <TextEditor
          class="w-full"
          :content="description"
          editable
          :fixed-menu="menuButtons"
          :placeholder="__('Describe your issue…')"
          editor-class="prose-sm max-w-none min-h-48 max-h-80 overflow-y-auto rounded-b-6 border border-t-0 border-outline-elevation-2 p-2"
          :upload-function="uploadInline"
          :extensions="editorExtensions"
          @change="description = $event"
        />
      </div>
      <div v-if="fields.length" class="field-grid w-full">
        <FormLayout :doc="model" :layout="layout" />
      </div>
      <PortalAttachments
        v-model="attachments"
        class="w-full"
        :restrictions="{ allowed_file_types: uploadableFileTypes(isAgent) }"
        :transport="uploadPrivately"
      />
    </div>
    <div class="flex w-full flex-col items-end pb-8 pt-8 sm:pt-[39px]">
      <Button
        size="md"
        theme="gray"
        variant="solid"
        :label="__('Create ticket')"
        :loading="isCreating || uploading > 0"
        @click="createTicket"
      />
      <p
        v-if="triedSubmit && missingFields.length"
        role="alert"
        class="mt-2 text-p-sm text-ink-red-6"
      >
        {{ __("Required: {0}", missingFields.join(", ")) }}
      </p>
    </div>
  </div>
  <PortalSkeleton v-else variant="form" :count="skeletonFieldCount" />
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import {
  Button,
  FormControl,
  call,
  createResource,
  useFileUpload,
} from "frappe-ui";
import { TextEditor } from "frappe-ui/experimental";
import { FormLayout, evaluateDependsOn } from "@framework/ui/FormLayout";
import DOMPurify from "dompurify";
import { applyFieldFilters } from "@helpdesk/shared/formScripts";
import { __ } from "@helpdesk/shared/translation";
import { HandleExcelPaste } from "@helpdesk/shared/tiptap";
import {
  isContentEmpty,
  parseLinkFilters,
  runAction,
  runFormScripts,
  uploadableFileTypes,
} from "@helpdesk/shared/utils";
// Relative, not `@app/`: the desk imports this component too.
import ApiOptionsField from "./ApiOptionsField.vue";
import PortalSkeleton from "../ui/PortalSkeleton.vue";
import PortalRelatedArticles from "../knowledge_base/PortalRelatedArticles.vue";
import PortalAttachments from "./PortalAttachments.vue";
import { useArticleSearch } from "../../composables/useArticleSearch";
import { useRememberedCount } from "../../composables/useRememberedCount";
import { getPriority, loadPriorities } from "../../stores/ticketMeta";

const UPLOAD_FOLDER = "Home/Helpdesk";
const SUGGESTION_LIMIT = 3;
// Longer Select lists get a search box if there are more than 10 results
const SEARCHABLE_FROM = 10;
const editorExtensions = [HandleExcelPaste];
// frappe-ui's default toolbar without Embed: the server strips iframes on save.
const menuButtons = [
  "Paragraph",
  [
    "Heading 1",
    "Heading 2",
    "Heading 3",
    "Heading 4",
    "Heading 5",
    "Heading 6",
  ],
  "Separator",
  "Bold",
  "Italic",
  "Strikethrough",
  "Link",
  "FontColor",
  "Separator",
  "Bullet List",
  "Numbered List",
  "Task List",
  "Separator",
  "Align Left",
  "Align Center",
  "Align Right",
  "Separator",
  "Image",
  "Video",
  "Blockquote",
  "Code",
  "Separator",
  "Horizontal Rule",
  [
    "InsertTable",
    "AddColumnBefore",
    "AddColumnAfter",
    "DeleteColumn",
    "AddRowBefore",
    "AddRowAfter",
    "DeleteRow",
    "MergeCells",
    "SplitCell",
    "ToggleHeaderColumn",
    "ToggleHeaderRow",
    "ToggleHeaderCell",
    "DeleteTable",
  ],
  "Separator",
  "TableOfContents",
  "Separator",
  "Undo",
  "Redo",
];

const props = withDefaults(
  defineProps<{
    template?: string;
    initialSubject?: string;
    origin?: Record<string, unknown>;
    isAgent?: boolean;
    suggestArticles?: boolean;
    dateFormat?: string;
    timeFormat?: string;
    // The desk's `$dialog`, so its form scripts render as on the ticket page.
    dialog?: (options: Record<string, unknown>) => unknown;
  }>(),
  { template: "Default", initialSubject: "" }
);

const emit = defineEmits<{
  created: [ticket: { name: string }];
  actions: [actions: any[]];
}>();

const router = useRouter();
const subject = ref(props.initialSubject);
const description = ref("");
const attachments = ref([]);
const isCreating = ref(false);
const uploading = ref(0);

// Queue keeps only `file_url`; the server links attachments by File name.
const uploadedByUrl = new Map();

const template = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket_template.api.get_one",
  params: { name: props.template },
  auto: true,
});
loadPriorities();

const skeletonFieldCount = useRememberedCount(
  // Per side: agents don't get the contact's `customer` field.
  `helpdesk-ticket-template-fields:${props.template}:${
    props.isAgent ? "agent" : "portal"
  }`,
  () => template.data?.fields?.length,
  0
);

const model = reactive<Record<string, any>>({});
// Original fields, for `applyFilters` to restore.
let oldFields: any[] = [];

watch(
  () => template.data,
  async (data) => {
    if (!data) return;
    if (data.description_template && isContentEmpty(description.value)) {
      description.value = data.description_template;
    }
    // Not structuredClone: it can't clone a reactive proxy.
    oldFields = JSON.parse(JSON.stringify(data.fields || []));
    // depends_on rules compare with ''; undefined would pass them.
    for (const row of data.fields || [])
      model[row.fieldname] ??=
        row.default ?? (row.fieldtype === "Check" ? 0 : "");
    const actions = await runFormScripts(
      data,
      { call, router },
      {
        doc: model,
        applyFilters,
        ...(props.dialog && { $dialog: props.dialog }),
      }
    );
    emit("actions", actions);
  }
);

// Check stays 1/0 as in Frappe, which depends_on rules and form scripts compare with.
watch(
  () =>
    (template.data?.fields || []).filter((row) => row.fieldtype === "Check"),
  (checks) => {
    for (const row of checks) {
      watch(
        () => model[row.fieldname],
        (value) => {
          if (typeof value === "boolean") model[row.fieldname] = value ? 1 : 0;
        },
        { flush: "sync" }
      );
    }
  }
);

// Removing an uploaded file deletes it, as the desk did, so no orphan File stays.
watch(attachments, (now, before) => {
  const kept = new Set(now.map((file) => file.file_url));
  for (const file of before) {
    const doc = uploadedByUrl.get(file.file_url);
    if (kept.has(file.file_url) || !doc) continue;
    uploadedByUrl.delete(file.file_url);
    call("frappe.client.delete", { doctype: "File", name: doc.name }).catch(
      () => {}
    );
  }
});

let created = false;
onBeforeUnmount(() => {
  if (created) return;
  for (const doc of uploadedByUrl.values()) {
    call("frappe.client.delete", { doctype: "File", name: doc.name }).catch(
      () => {}
    );
  }
});

function applyFilters(fieldname: string, filters: any = null) {
  applyFieldFilters(template.data.fields, fieldname, filters, model, oldFields);
}

function runChangeHandlers(row, value) {
  template.data?._customOnChange?.[row.fieldname]?.forEach((handler) =>
    handler(value, row.fieldtype)
  );
}

const visibleFields = computed(() =>
  (template.data?.fields || []).filter((row) =>
    evaluateDependsOn(row.depends_on, model)
  )
);

function isRequired(row) {
  return (
    Boolean(row.required) ||
    Boolean(
      row.mandatory_depends_on &&
        evaluateDependsOn(row.mandatory_depends_on, model)
    )
  );
}

const missingFields = computed(() => [
  ...(subject.value.trim() ? [] : [__("Subject")]),
  ...(isContentEmpty(description.value) ? [__("Description")] : []),
  ...visibleFields.value
    .filter((row) => isRequired(row) && !model[row.fieldname])
    .map((row) => __(row.label)),
]);

// Shown once a submit is tried, then kept live as fields fill.
const triedSubmit = ref(false);

// Links keep `target` so they never navigate away from a half-filled form.
const about = computed(() => {
  const body = DOMPurify.sanitize(template.data?.about || "", {
    ADD_ATTR: ["target"],
    RETURN_DOM: true,
  });
  body
    .querySelectorAll("a[target]")
    .forEach((link) => link.setAttribute("rel", "noopener noreferrer"));
  return body.innerHTML;
});
// The desk's TicketNew has no suggestions: an empty query never fetches.
const suggestionQuery = computed(() =>
  props.suggestArticles ? subject.value : ""
);
const suggestions = useArticleSearch(suggestionQuery, {
  limit: SUGGESTION_LIMIT,
});

// Only priority shows its description, as on the ticket page.
const priorityHint = computed(
  () => getPriority(model.priority)?.description?.trim() || undefined
);

function defaultPlaceholder(row) {
  return row.url_method || ["Select", "Link", "Check"].includes(row.fieldtype)
    ? __("Select an option")
    : __("Type something");
}

// Date formats are unset until the config arrives.
function uiFor(row) {
  if (row.url_method)
    return { component: ApiOptionsField, props: { url: row.url_method } };
  const options = (row.options || "").split("\n").filter(Boolean);
  if (row.fieldtype === "Select" && options.length > SEARCHABLE_FROM) {
    const list = options.map((value) => ({ label: __(value), value }));
    return { component: ApiOptionsField, props: { options: list } };
  }
  // `padded` gives the Check the inputs' height, so `.field-grid` can row it with them.
  if (row.fieldtype === "Check") return { props: { padded: true } };
  if (!props.dateFormat) return undefined;
  if (row.fieldtype === "Datetime")
    return { props: { format: `${props.dateFormat} ${props.timeFormat}` } };
  if (row.fieldtype === "Date") return { props: { format: props.dateFormat } };
}

const fields = computed(() =>
  (template.data?.fields || []).map((row) => ({
    fieldname: row.fieldname,
    fieldtype: row.fieldtype,
    label: __(row.label),
    options: row.options,
    reqd: Boolean(row.required),
    placeholder: row.placeholder || defaultPlaceholder(row),
    description: row.fieldname === "priority" ? priorityHint.value : undefined,
    dependsOn: row.depends_on,
    mandatoryDependsOn: row.mandatory_depends_on,
    readOnlyDependsOn: row.read_only_depends_on,
    filters: row.link_filters ? parseLinkFilters(row.link_filters) : undefined,
    readOnly: Boolean(row.read_only || row.disabled),
    ui: {
      ...uiFor(row),
      on: { change: (value) => runChangeHandlers(row, value) },
    },
  }))
);

// One column, laid out as a grid by `.field-grid`, so cells keep their width as
// `depends_on` fields come and go. FormLayout hides those fields itself.
const layout = computed(() => [
  {
    sections: [
      {
        hideLabel: true,
        hideBorder: true,
        columns: [{ fields: fields.value }],
      },
    ],
  },
]);

function uploadPrivately(file, _args, { signal, onProgress }) {
  uploading.value += 1;
  return useFileUpload()
    .upload(file, {
      private: true,
      folder: UPLOAD_FOLDER,
      signal,
      onProgress: ({ loaded, total }) => onProgress(loaded, total),
    })
    .then((doc) => {
      uploadedByUrl.set(doc.file_url, doc);
      return doc;
    })
    .finally(() => (uploading.value -= 1));
}

// Counted so a ticket is never created around a half-uploaded image.
function uploadInline(file: File) {
  uploading.value += 1;
  return useFileUpload()
    .upload(file, { private: true })
    .finally(() => (uploading.value -= 1));
}

function createTicket() {
  triedSubmit.value = true;
  if (missingFields.value.length || uploading.value || isCreating.value) return;
  return runAction(
    async () => {
      // call(), not a resource: the desk's resource error handler toasts again.
      const ticket = await call("helpdesk.helpdesk.doctype.hd_ticket.api.new", {
        doc: {
          subject: subject.value.trim(),
          description: description.value,
          template: props.template,
          ...model,
        },
        attachments: attachments.value.map((file) =>
          uploadedByUrl.get(file.file_url)
        ),
        origin: props.origin,
      });
      created = true;
      emit("created", ticket);
    },
    {
      busy: isCreating,
      success: __("Ticket created"),
      fallback: __("Could not create the ticket"),
    }
  );
}
</script>

<style scoped>
/* Sized by the form, not the viewport: the desk renders it beside a sidebar. */
.field-grid {
  container-type: inline-size;
}
@container (min-width: 32rem) {
  .field-grid :deep(.column) {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  /* Checks have no label above, so sit them on the inputs' row. */
  .field-grid :deep(.field[data-fieldtype="Check"]) {
    align-self: end;
  }
}
</style>
