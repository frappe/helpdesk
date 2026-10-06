<template>
  <div class="flex flex-col">
    <div class="flex flex-col gap-6">
      <div
        v-for="toggle in toggles"
        :key="toggle.fieldname"
        class="flex items-center justify-between"
      >
        <div class="flex flex-col gap-1">
          <span class="text-base-medium text-ink-gray-8">
            {{ toggle.label }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{ toggle.description }}
          </span>
        </div>
        <Switch
          :model-value="Boolean(settings.doc?.[toggle.fieldname])"
          @update:model-value="(value) => save({ [toggle.fieldname]: value })"
        />
      </div>
      <div class="flex items-center justify-between gap-6">
        <div class="flex flex-col gap-1">
          <span class="text-base-medium text-ink-gray-8">
            {{ __("Pinned categories") }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{
              __(
                "Only these categories will appear on the knowledge base home page. Leave empty to show all of them."
              )
            }}
          </span>
        </div>
        <MultiSelect
          class="w-48 shrink-0"
          :model-value="pinned"
          :options="categoryOptions"
          :placeholder="__('All categories')"
          @update:model-value="pin"
        />
      </div>
    </div>
    <BannerPicker
      class="mt-8"
      :image="settings.doc?.banner_image || ''"
      :preset="settings.doc?.banner_preset || ''"
      @change="save"
    />
    <HeaderLinks class="mt-8" @saved="emit('saved')" />
  </div>
</template>

<script setup lang="ts">
import { __ } from "../translation";
import {
  call,
  createDocumentResource,
  createListResource,
  MultiSelect,
  Switch,
  toast,
} from "frappe-ui";
import { computed, ref, watch } from "vue";
import BannerPicker from "./BannerPicker.vue";
import HeaderLinks from "./HeaderLinks.vue";

// computed, so labels follow a translation load
const toggles = computed(() => [
  {
    fieldname: "public_knowledge_base",
    label: __("Make knowledge base public"),
    description: __("Anyone will be able to read articles without logging in."),
  },
  {
    fieldname: "allow_anonymous_article_voting",
    label: __("Allow guests to vote on articles"),
    description: __(
      "Visitors who aren't logged in will be able to mark articles as helpful or not."
    ),
  },
]);

const settings = createDocumentResource({
  doctype: "HD Settings",
  name: "HD Settings",
});

const emit = defineEmits<{ saved: [] }>();

const categories = createListResource({
  doctype: "HD Article Category",
  fields: ["name", "category_name", "pinned"],
  orderBy: "category_name asc",
  pageLength: 999,
  auto: true,
});

const categoryOptions = computed(() =>
  (categories.data || []).map((row) => ({
    label: row.category_name,
    value: row.name,
  }))
);

const pinned = ref<string[]>([]);

watch(
  () => categories.data,
  (rows) =>
    (pinned.value = (rows || [])
      .filter((row) => row.pinned)
      .map((row) => row.name)),
  { immediate: true }
);

async function pin(values: string[]) {
  const changed = categoryOptions.value
    .map(({ value }) => value)
    .filter((name) => values.includes(name) !== pinned.value.includes(name));
  pinned.value = values;
  const { failed_docs } = await call("frappe.client.bulk_update", {
    docs: changed.map((name) => ({
      doctype: "HD Article Category",
      docname: name,
      pinned: values.includes(name) ? 1 : 0,
    })),
  });
  if (failed_docs.length) {
    toast.error(__("Could not update the pinned categories"));
    categories.reload();
    return;
  }
  toast.success(__("Settings updated"));
}

function save(values: Record<string, string | boolean>) {
  settings.setValue.submit(values, {
    onSuccess: () => {
      toast.success(__("Settings updated"));
      emit("saved");
    },
  });
}
</script>
