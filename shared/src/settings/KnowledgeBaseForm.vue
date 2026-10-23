<template>
  <Transition
    enter-from-class="opacity-0"
    enter-active-class="transition-opacity duration-200 motion-reduce:transition-none"
  >
    <div v-if="draft" class="space-y-11">
      <section>
        <h2 class="text-md-semibold text-ink-gray-8">{{ __("Access") }}</h2>
        <div class="mt-2 divide-y divide-outline-gray-1">
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
              @update:model-value="
                (value) => setToggle(toggle.fieldname, value)
              "
            />
          </SettingsRow>
        </div>
      </section>
      <section>
        <h2 class="text-md-semibold text-ink-gray-8">
          {{ __("Customize home page") }}
        </h2>
        <div class="mt-2 divide-y divide-outline-gray-1 [&>*]:py-3.5">
          <PinnedCategories
            v-model:pinned="draft.pinned"
            :categories="categoryOptions"
            :save="savePinsAndNotify"
          />
          <BannerPicker
            :image="draft.banner_image"
            :preset="draft.banner_preset"
            @change="(value) => Object.assign(draft, value)"
          />
        </div>
      </section>
      <section>
        <h2 class="text-md-semibold text-ink-gray-8">{{ __("Header") }}</h2>
        <div class="mt-2 divide-y divide-outline-gray-1 [&>*]:py-3.5">
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
          <HeaderLinks v-model="draft.links" />
        </div>
      </section>
    </div>
    <SettingsFormSkeleton
      v-else
      :sections="[
        { title: __('Access'), rows: accessToggles.length },
        { title: __('Customize home page'), panels: [50, 180] },
        { title: __('Header'), rows: 1, panels: [96] },
      ]"
    />
  </Transition>
</template>

<script setup lang="ts">
import { __ } from "../translation";
import { SettingsRow, Switch } from "frappe-ui";
import { computed } from "vue";
import BannerPicker from "./BannerPicker.vue";
import HeaderLinks from "./HeaderLinks.vue";
import PinnedCategories from "./PinnedCategories.vue";
import SettingsFormSkeleton from "./SettingsFormSkeleton.vue";
import { useKnowledgeBaseDraft } from "./knowledgeBaseDraft";

// Switches and the pin dialog save at once; the rest waits for Save.
const { draft, settings, setToggle, savePins, categoryOptions } =
  useKnowledgeBaseDraft();

const emit = defineEmits<{ pinsSaved: [] }>();

async function savePinsAndNotify(pinned: string[]) {
  const saved = await savePins(pinned);
  if (saved) emit("pinsSaved");
  return saved;
}

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
