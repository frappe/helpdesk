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
    </div>
    <hr class="my-8" />
    <div class="text-base-semibold text-ink-gray-9">
      {{ __("Customize Knowledge Base") }}
    </div>
    <BannerPicker
      class="mt-6"
      :image="settings.doc?.banner_image || ''"
      :preset="settings.doc?.banner_preset || ''"
      @change="save"
    />
    <HeaderLinks
      class="mt-8"
      :links="settings.doc?.portal_header_links || []"
      @saved="onLinksSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { __ } from "../translation";
import { createDocumentResource, Switch, toast } from "frappe-ui";
import { computed } from "vue";
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

function save(values: Record<string, string | boolean>) {
  settings.setValue.submit(values, {
    onSuccess: () => {
      toast.success(__("Settings updated"));
      emit("saved");
    },
  });
}

function onLinksSaved() {
  settings.reload();
  emit("saved");
}
</script>
