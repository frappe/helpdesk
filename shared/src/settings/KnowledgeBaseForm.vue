<template>
  <div v-if="draft" class="flex flex-col">
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
        <Switch v-model="draft[toggle.fieldname]" />
      </div>
    </div>
    <PinnedCategories
      v-model="draft.pinned"
      class="mt-8"
      :categories="categoryOptions"
    />
    <BannerPicker
      class="mt-8"
      :image="draft.banner_image"
      :preset="draft.banner_preset"
      @change="(value) => Object.assign(draft, value)"
    />
    <HeaderLinks v-model="draft.links" class="mt-8" />
  </div>
</template>

<script setup lang="ts">
import { __ } from "../translation";
import { Switch } from "frappe-ui";
import { computed } from "vue";
import BannerPicker from "./BannerPicker.vue";
import HeaderLinks from "./HeaderLinks.vue";
import PinnedCategories from "./PinnedCategories.vue";
import { useKnowledgeBaseDraft } from "./knowledgeBaseDraft";

// Changes wait for the host's Save button; see knowledgeBaseDraft.ts.
const { draft, categoryOptions } = useKnowledgeBaseDraft();

// computed, so labels follow a translation load
const toggles = computed(
  () =>
    [
      {
        fieldname: "public_knowledge_base",
        label: __("Make knowledge base public"),
        description: __(
          "Anyone will be able to read articles without logging in."
        ),
      },
      {
        fieldname: "allow_anonymous_article_voting",
        label: __("Allow guests to vote on articles"),
        description: __(
          "Visitors who aren't logged in will be able to mark articles as helpful or not."
        ),
      },
    ] as const
);
</script>
