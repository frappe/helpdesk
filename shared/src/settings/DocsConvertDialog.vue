<template>
  <Dialog v-model:open="open" :title="title">
    <template #default>
      <div class="space-y-3">
        <p
          v-if="matching"
          class="rounded bg-surface-amber-2 p-2 text-p-sm text-ink-gray-9"
        >
          {{ __("An Article with this title already exists:") }}
          <a
            :href="articleHref(matching.name)"
            target="_blank"
            rel="noopener"
            class="underline"
            >{{ matching.title }}</a
          >
        </p>
        <Combobox
          v-model="category"
          class="w-full"
          :options="options"
          :placeholder="__('Select Category')"
        />
        <p v-if="error" class="text-p-sm text-ink-red-3">{{ error }}</p>
      </div>
    </template>
    <template #actions>
      <Button
        variant="solid"
        class="w-full"
        :label="__('Convert')"
        :loading="busy"
        :disabled="!category"
        @click="submit"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { call, Button, Combobox, Dialog } from "frappe-ui";
import { computed, ref, watch } from "vue";
import { __ } from "../translation";
import { getErrorMessage } from "../utils";
import { articleHref, pagesLabel } from "./docsLinks";

const API = "helpdesk.api.docs_source";

const props = defineProps<{
  routes: string[];
  matching?: { name: string; title: string } | null;
  bulk?: boolean;
}>();
const emit = defineEmits<{ done: [article?: string] }>();
const open = defineModel<boolean>("open", { default: false });

const category = ref("");
const options = ref<{ value: string; label: string }[]>([]);
const busy = ref(false);
const error = ref("");

const title = computed(() =>
  props.bulk
    ? pagesLabel(props.routes.length)
    : __("Convert to article")
);

watch(open, async (shown) => {
  if (!shown) return;
  category.value = "";
  error.value = "";
  try {
    const rows = await call("helpdesk.api.knowledge_base.get_category_options");
    options.value = rows.map(({ value, label }) => ({ value, label }));
  } catch (e) {
    error.value = getErrorMessage(e);
  }
});

async function submit() {
  busy.value = true;
  error.value = "";
  try {
    if (props.bulk) {
      await call(`${API}.bulk_convert_docs_pages`, {
        routes: props.routes,
        category: category.value,
      });
      emit("done");
    } else {
      const name = await call(`${API}.convert_docs_page`, {
        route: props.routes[0],
        category: category.value,
      });
      window.open(articleHref(name), "_blank", "noopener");
      emit("done", name);
    }
    open.value = false;
  } catch (e) {
    error.value = getErrorMessage(e);
  } finally {
    busy.value = false;
  }
}
</script>
