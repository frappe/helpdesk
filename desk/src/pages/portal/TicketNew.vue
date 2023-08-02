<template>
  <div class="pb-8 text-base text-gray-700">
    <div class="flex flex-col gap-4">
      <TopBar title="New ticket" :back-to="{ name: CUSTOMER_PORTAL_LANDING }" />
      <div
        v-if="template.data?.about"
        class="prose prose-sm mx-9 max-w-full"
        v-html="sanitize(template.data.about)"
      />
      <div class="mx-9 grid grid-cols-3 gap-4">
        <div
          v-for="field in visibleFields"
          :key="field.fieldname"
          class="space-y-2"
        >
          <div class="text-xs">{{ field.label }}</div>
          <div v-if="field.url_method">
            <Autocomplete
              placeholder="Select an option"
              :options="serverScriptOptions[field.fieldname]"
              :value="customFields[field.fieldname]"
              @change="(v) => (customFields[field.fieldname] = v.value)"
            />
          </div>
          <div v-else-if="field.fieldtype === 'Link' && field.options">
            <SearchComplete
              :doctype="field.options"
              @change="(v) => (customFields[field.fieldname] = v.value)"
            />
          </div>
          <div v-else-if="field.fieldtype === 'Select'">
            <Autocomplete
              placeholder="Select an option"
              :options="selectOptions(field.options)"
              :value="customFields[field.fieldname]"
              @change="(v) => (customFields[field.fieldname] = v.value)"
            />
          </div>
          <div v-else-if="field.fieldtype === 'Data'">
            <FormControl
              type="text"
              placeholder="Type something"
              :value="customFields[field.fieldname]"
              @input="(v) => (customFields[field.fieldname] = v.value)"
            />
          </div>
        </div>
      </div>
      <div
        v-if="!isEmpty(articles.data)"
        class="mx-9 flex flex-col gap-4 rounded-lg border bg-yellow-50 p-4"
      >
        <div class="font-medium">
          📚 Did you know? These articles might cover what you looking for!
        </div>
        <RouterLink
          v-for="article in articles.data"
          :key="article.name"
          class="group flex cursor-pointer gap-2 transition hover:text-gray-900"
          :to="getArticleLink(article.name, article.title)"
          target="_blank"
        >
          {{ article.title }}
          <div class="opacity-0 group-hover:opacity-100">&rightarrow;</div>
        </RouterLink>
      </div>
      <div class="mx-9 space-y-2">
        <Input
          v-model="subject"
          label="Subject"
          placeholder="A short description"
          @input="(v) => searchArticles(v)"
        />
        <TextEditor
          ref="textEditor"
          placeholder="Detailed explanation"
          :content="description"
          @change="(v) => (description = v)"
        >
          <template #bottom="{ editor }">
            <TextEditorBottom
              v-model:attachments="attachments"
              :editor="editor"
            >
              <template #actions-right>
                <Button
                  label="Create"
                  :disabled="isDisabled"
                  theme="gray"
                  variant="solid"
                  @click="create"
                />
              </template>
            </TextEditorBottom>
          </template>
        </TextEditor>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted, computed, reactive, onMounted } from "vue";
import { RouterLink, useRouter } from "vue-router";
import {
  createResource,
  createListResource,
  debounce,
  Autocomplete,
  Button,
  Input,
} from "frappe-ui";
import sanitizeHtml from "sanitize-html";
import { isEmpty } from "lodash";
import {
  CUSTOMER_PORTAL_LANDING,
  CUSTOMER_PORTAL_TICKET,
  KB_PUBLIC_ARTICLE,
} from "@/router";
import { useConfigStore } from "@/stores/config";
import { createToast } from "@/utils/toasts";
import SearchComplete from "@/components/SearchComplete.vue";
import TextEditor from "@/components/text-editor/TextEditor.vue";
import TextEditorBottom from "@/components/text-editor/TextEditorBottom.vue";
import TopBar from "@/components/TopBar.vue";

const props = defineProps({
  templateId: {
    type: String,
    required: false,
    default: "Default",
  },
});

const router = useRouter();
const configStore = useConfigStore();
const textEditor = ref();

const subject = ref("");
const description = ref("");
const attachments = ref([]);
const customFields = reactive({});
const serverScriptOptions = reactive({});

const template = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket_template.api.get_one",
  makeParams: () => ({
    name: props.templateId,
  }),
  auto: true,
  onSuccess: fetchOptionsFromServerScript,
});

const articles = createListResource({
  doctype: "HD Article",
  fields: ["name", "title"],
  pageLimit: 5,
  debounce: 500,
});

const visibleFields = computed(() =>
  template.data?.fields.filter((f) => !f.hide_from_customer)
);
const r = createResource({
  url: "helpdesk.api.ticket.create_new",
  validate(params) {
    for (const field of visibleFields.value || []) {
      if (field.required && isEmpty(params.values[field.fieldname])) {
        return `${field.label} is required`;
      }
    }

    if (isEmpty(params.values.subject)) return "Subject is required";
    if (isEmpty(params.values.description)) return "Description is required";
  },
  onError(error) {
    const title = error.message ? error.message : error.messages?.join("\n");

    createToast({
      title,
      icon: "x",
      iconClasses: "text-red-500",
    });
  },
  onSuccess(data) {
    router.push({
      name: CUSTOMER_PORTAL_TICKET,
      params: {
        ticketId: data.name,
      },
    });
  },
});

const create = debounce(() => {
  const values = {
    subject: subject.value,
    description: description.value,
  };

  Object.assign(values, customFields);

  r.submit({
    values,
    template: props.templateId,
    attachments: attachments.value,
    via_customer_portal: true,
  });
}, 500);

const isDisabled = computed(
  () => r.loading || isEmpty(subject.value) || textEditor.value?.editor.isEmpty
);

function sanitize(html: string) {
  return sanitizeHtml(html, {
    allowedTags: sanitizeHtml.defaults.allowedTags.concat(["img"]),
  });
}

function getArticleLink(name: string, title: string) {
  return {
    name: KB_PUBLIC_ARTICLE,
    params: {
      articleId: name,
      articleTitleSlug: title.toLowerCase().replaceAll(" ", "-"),
    },
  };
}

function selectOptions(options: string) {
  return options.split("\n").map((o) => ({
    label: o,
    value: o,
  }));
}

function searchArticles(term: string) {
  if (term.length < 5) {
    delete articles.data;
    return;
  }

  articles.update({
    filters: {
      title: ["like", `%${term}%`],
    },
  });

  articles.reload();
}

function fetchOptionsFromServerScript() {
  visibleFields.value.forEach((field) => {
    if (field.url_method) {
      createResource({
        url: field.url_method,
        auto: true,
        onSuccess: (data) => {
          const options = data.map((o) => ({
            label: o,
            value: o,
          }));
          serverScriptOptions[field.fieldname] = options;
        },
      });
    }
  });
}

onMounted(() => configStore.setTitle("New ticket"));
onUnmounted(() => configStore.setTitle());
</script>
