<template>
  <div class="flex flex-col gap-3">
    <div class="flex flex-col gap-1">
      <span class="text-base-medium text-ink-gray-8">
        {{ __("Quick links") }}
      </span>
      <span class="text-p-sm text-ink-gray-6">
        {{ __("Appear at the top right of every knowledge base page.") }}
      </span>
    </div>
    <div class="rounded-5 border border-outline-gray-2 px-1 text-sm">
      <List
        v-if="rows.length"
        :columns="columns"
        :row-height="44"
        class="[--list-gap:1rem] [--list-row-padding-x:0.5rem]"
      >
        <ListHeader>
          <ListHeaderCell class="ms-2">{{ __("Label") }}</ListHeaderCell>
          <ListHeaderCell class="ms-2">{{ __("URL") }}</ListHeaderCell>
          <ListHeaderCell class="justify-center">
            {{ __("New tab") }}
          </ListHeaderCell>
          <ListHeaderCell />
        </ListHeader>
        <ListRows :items="rows" v-slot="{ item: row, index }">
          <ListRow>
            <ListCell>
              <TextInput
                v-model="row.label"
                class="w-full"
                variant="ghost"
                :placeholder="__('Contact sales')"
              />
            </ListCell>
            <ListCell>
              <TextInput
                v-model="row.url"
                class="w-full"
                variant="ghost"
                :placeholder="__('https://example.com/contact')"
              />
            </ListCell>
            <ListCell class="justify-center">
              <Checkbox v-model="row.open_in_new_tab" />
            </ListCell>
            <ListCell>
              <Button
                variant="ghost"
                icon="lucide-trash-2"
                :label="__('Delete')"
                @click="rows.splice(index, 1)"
              />
            </ListCell>
          </ListRow>
        </ListRows>
      </List>
      <div v-else class="p-4 text-center text-ink-gray-5">
        {{ __("No links yet. Add one to show it in the portal header") }}
      </div>
    </div>
    <div class="flex items-center justify-between">
      <Button
        variant="subtle"
        icon-left="lucide-plus"
        :label="__('Add link')"
        @click="rows.push({ label: '', url: '', open_in_new_tab: false })"
      />
      <Button
        v-if="isDirty"
        variant="solid"
        :label="__('Save')"
        :loading="saving"
        @click="save"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "../translation";
import { getErrorMessage, isSafeLink } from "../utils";
import {
  Button,
  call,
  Checkbox,
  createResource,
  TextInput,
  toast,
} from "frappe-ui";
import {
  List,
  ListCell,
  ListHeader,
  ListHeaderCell,
  ListRow,
  ListRows,
} from "frappe-ui/list";
import { computed, ref, watch } from "vue";

type HeaderLink = { label: string; url: string; open_in_new_tab: boolean };

const emit = defineEmits<{ saved: [] }>();

// Kept as a knowledge base form script, the way field dependencies are; its last line holds the rows.
const SCRIPT_NAME = "Knowledge Base Quick Links";
const JSON_MARKER = "//JSON: ";

const columns = ["minmax(0,1fr)", "minmax(0,2fr)", "64px", "32px"];

const rows = ref<HeaderLink[]>([]);

// Only the editable fields, trimmed, so formatting alone doesn't count as an edit.
function pick(links: HeaderLink[]) {
  return links.map(({ label, url, open_in_new_tab }) => ({
    label: label?.trim() || "",
    url: url?.trim() || "",
    open_in_new_tab: Boolean(open_in_new_tab),
  }));
}

const script = createResource({
  url: "frappe.client.get_value",
  params: {
    doctype: "HD Form Script",
    filters: { name: SCRIPT_NAME },
    fieldname: "script",
  },
  auto: true,
});

const saved = computed(() => {
  const source = script.data?.script || "";
  return source.includes(JSON_MARKER) ? source.split(JSON_MARKER).pop() : "[]";
});

watch(saved, (links) => (rows.value = JSON.parse(links)), { immediate: true });

function scriptFor(links: HeaderLink[]) {
  const json = JSON.stringify(links);
  return `function setupForm() {\n  return { links: ${json} };\n}\n${JSON_MARKER}${json}`;
}

const saving = ref(false);

async function saveLinks(links: HeaderLink[]) {
  saving.value = true;
  try {
    if (script.data?.script) {
      await call("frappe.client.set_value", {
        doctype: "HD Form Script",
        name: SCRIPT_NAME,
        fieldname: "script",
        value: scriptFor(links),
      });
    } else {
      await call("frappe.client.insert", {
        doc: {
          doctype: "HD Form Script",
          name: SCRIPT_NAME,
          dt: "HD Ticket",
          apply_to_knowledge_base: 1,
          enabled: 1,
          script: scriptFor(links),
        },
      });
    }
    toast.success(__("Settings updated"));
    script.reload();
    emit("saved");
  } catch (error) {
    getErrorMessage(error, true);
  } finally {
    saving.value = false;
  }
}

function save() {
  const links = pick(rows.value).filter((link) => link.label || link.url);
  const incomplete = links.find((link) => !link.label || !link.url);
  if (incomplete) return toast.error(__("Each link needs a label and a URL"));
  const unsafe = links.find((link) => !isSafeLink(link.url));
  if (unsafe) {
    return toast.error(
      __("{0}: use a web address, an email link or a path starting with /", [
        unsafe.label,
      ])
    );
  }
  saveLinks(links);
}

const isDirty = computed(
  () =>
    JSON.stringify(pick(rows.value)) !==
    JSON.stringify(pick(JSON.parse(saved.value)))
);
</script>
