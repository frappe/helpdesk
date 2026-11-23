<template>
  <Tabs v-model="tab" :tabs="tabs">
    <template #tab-panel="{ tab: { value } }">
      <Transition
        enter-from-class="opacity-0"
        enter-active-class="transition-opacity duration-200 motion-reduce:transition-none"
      >
        <div
          v-if="draft"
          class="divide-y divide-outline-gray-1 pt-2 [&>*]:py-3.5"
        >
          <template v-if="value === 'home'">
            <SettingsRow
              :title="__('Title')"
              :description="__('Heading shown in the banner.')"
            >
              <TextInput
                v-model="draft.banner_title"
                class="w-72"
                :placeholder="defaultBannerTitle()"
              />
            </SettingsRow>
            <SettingsRow
              :title="__('Subtitle')"
              :description="__('Text under the heading.')"
            >
              <div class="w-72">
                <Textarea
                  v-model="draft.banner_subtitle"
                  class="max-h-40"
                  :rows="2"
                  :placeholder="defaultBannerSubtitle(settings.doc?.brand_name)"
                />
              </div>
            </SettingsRow>
            <BannerPicker
              :image="draft.banner_image"
              :preset="draft.banner_preset"
              @change="(change) => Object.assign(draft, change)"
            />
            <PinnedList
              v-model:pinned="draft.pinned"
              kind="categories"
              :items="categoryOptions"
              :save="(pinned) => savePinsAndNotify('categories', pinned)"
            />
            <PinnedList
              v-model:pinned="draft.pinned_articles"
              kind="articles"
              :items="articleOptions"
              :search="searchArticles"
              :save="(pinned) => savePinsAndNotify('articles', pinned)"
            />
          </template>
          <template v-else-if="value === 'header'">
            <!-- Stored inverted so unset (existing sites) means shown. -->
            <SettingsRow
              label-for=""
              :title="__('Show Raise a ticket button')"
              :description="
                __(
                  'Logged-in customers will see a Raise a ticket button in the knowledge base header.'
                )
              "
            >
              <Switch
                :aria-label="__('Show Raise a ticket button')"
                :model-value="!settings.doc?.hide_raise_ticket_button"
                @update:model-value="
                  (show) => setToggle('hide_raise_ticket_button', !show)
                "
              />
            </SettingsRow>
            <LinkTable
              v-model="draft.links"
              :title="__('Quick links')"
              :description="
                __(
                  'Add links to your website, docs or social pages. They will appear at the top right of every knowledge base page.'
                )
              "
            />
          </template>
          <FooterSettings
            v-else-if="value === 'footer'"
            v-model="draft.footer"
          />
          <template v-else>
            <!-- label-for="": a title click must not flip the switch, so aria-label names it -->
            <SettingsRow
              label-for=""
              v-for="toggle in accessToggles"
              :key="toggle.fieldname"
              :title="toggle.label"
              :description="toggle.description"
            >
              <Switch
                :aria-label="toggle.label"
                :model-value="Boolean(settings.doc?.[toggle.fieldname])"
                :disabled="
                  toggle.fieldname === 'allow_anonymous_article_voting' &&
                  !settings.doc?.public_knowledge_base &&
                  !settings.doc?.[toggle.fieldname]
                "
                @update:model-value="(on) => setToggle(toggle.fieldname, on)"
              />
            </SettingsRow>
          </template>
        </div>
        <SettingsFormSkeleton v-else :sections="[skeletons[value]]" />
      </Transition>
    </template>
  </Tabs>
</template>

<script setup lang="ts">
import { __ } from "../translation";
import { SettingsRow, Switch, Tabs, Textarea, TextInput } from "frappe-ui";
import { computed, watch } from "vue";
import {
  defaultBannerSubtitle,
  defaultBannerTitle,
} from "../knowledgeBaseBanner";
import BannerPicker from "./BannerPicker.vue";
import FooterSettings from "./FooterSettings.vue";
import LinkTable from "./LinkTable.vue";
import PinnedList from "./PinnedList.vue";
import SettingsFormSkeleton from "./SettingsFormSkeleton.vue";
import { type PinKind, useKnowledgeBaseDraft } from "./knowledgeBaseDraft";

// Switches and the pin dialog save at once; the rest waits for Save.
const {
  draft,
  settings,
  setToggle,
  savePins,
  categoryOptions,
  articleOptions,
  searchArticles,
} = useKnowledgeBaseDraft();

const emit = defineEmits<{ pinsSaved: [] }>();

async function savePinsAndNotify(kind: PinKind, pinned: string[]) {
  const saved = await savePins(kind, pinned);
  if (saved) emit("pinsSaved");
  return saved;
}

const tab = defineModel<string>("tab", { default: "home" });

const tabs = computed(() => [
  { value: "home", label: __("Home page") },
  { value: "header", label: __("Header") },
  { value: "footer", label: __("Footer") },
  { value: "access", label: __("Access") },
]);

watch(
  tab,
  (value) => {
    if (!tabs.value.some((option) => option.value === value))
      tab.value = "home";
  },
  { immediate: true }
);

const skeletons = {
  home: { rows: 2, panels: [180, 50, 50] },
  header: { rows: 1, panels: [96] },
  footer: { rows: 1 },
  access: { rows: 2 },
};

// computed, so labels follow a translation load
const accessToggles = computed(
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
