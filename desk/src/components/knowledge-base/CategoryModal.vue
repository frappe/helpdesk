<template>
  <Dialog v-model:open="showDialog" :title="dialogTitle" size="md">
    <template #default>
      <!-- Tree order: the parent sits above, the category hangs below it.
           Rows 0fr → 1fr grows the dialog to the row's height instead of jumping. -->
      <Transition
        appear
        enter-from-class="grid-rows-[0fr] opacity-0"
        enter-active-class="overflow-hidden transition-[grid-template-rows,opacity] duration-200 ease-out motion-reduce:transition-none"
        enter-to-class="grid-rows-[1fr]"
        leave-from-class="grid-rows-[1fr]"
        leave-active-class="overflow-hidden transition-[grid-template-rows,opacity] duration-150 delay-200 ease-in motion-reduce:transition-none"
        leave-to-class="grid-rows-[0fr] opacity-0"
        @after-leave="onUndrawn"
      >
        <div v-if="drawn" class="grid">
          <div class="min-h-0">
            <div class="flex items-center gap-2 pb-2">
              <span
                class="grid size-8 shrink-0 place-items-center rounded-4 bg-surface-gray-2 text-ink-gray-7"
                aria-hidden="true"
              >
                <span :class="parentIcon" class="size-4" />
              </span>
              <Combobox
                v-model="parent"
                :options="parentOptions"
                :placeholder="__('Choose a parent category')"
                :aria-label="__('Parent category')"
                size="md"
                class="flex-1"
              />
              <Tooltip :text="__('Remove parent')">
                <!-- Sized like the dialog's close button, which sits right above it. -->
                <Button
                  variant="ghost"
                  :aria-label="__('Remove parent')"
                  @click="unnest"
                >
                  <template #icon>
                    <span class="lucide-link-2-off size-4 text-ink-gray-9" />
                  </template>
                </Button>
              </Tooltip>
            </div>
          </div>
        </div>
      </Transition>

      <div
        class="relative flex items-center gap-2 transition-[padding] duration-200 ease-out motion-reduce:transition-none"
        :class="drawn ? 'pl-10' : 'pl-0 delay-150'"
      >
        <!-- Icon to icon: one dotted path with a rounded elbow, from the
             parent's tile down and across. A solid mask stroke draws it in. -->
        <Transition
          appear
          :duration="{ enter: 450, leave: 200 }"
          enter-from-class="[&_.kb-reveal]:[stroke-dashoffset:1]"
          enter-active-class="[&_.kb-reveal]:[transition:stroke-dashoffset_300ms_cubic-bezier(0.2,0,0,1)_150ms] motion-reduce:[&_.kb-reveal]:[transition:none]"
          leave-active-class="[&_.kb-reveal]:[transition:stroke-dashoffset_200ms_ease-in] motion-reduce:[&_.kb-reveal]:[transition:none]"
          leave-to-class="[&_.kb-reveal]:[stroke-dashoffset:1]"
        >
          <svg
            v-if="drawn"
            aria-hidden="true"
            class="absolute -top-2 left-4 h-6 w-5 overflow-visible text-[--outline-gray-5]"
            viewBox="0 0 20 24"
            fill="none"
          >
            <mask
              id="kb-category-elbow"
              maskUnits="userSpaceOnUse"
              x="-4"
              y="-4"
              width="28"
              height="32"
            >
              <path
                class="kb-reveal"
                :d="ELBOW"
                stroke="white"
                stroke-width="4"
                pathLength="1"
                stroke-dasharray="1"
              />
            </mask>
            <path
              :d="ELBOW"
              mask="url(#kb-category-elbow)"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-dasharray="0 3"
            />
          </svg>
        </Transition>
        <IconPicker v-model="icon" />
        <TextInput
          ref="nameInput"
          v-model="newTitle"
          class="flex-1"
          size="md"
          maxlength="50"
          :placeholder="nesting ? __('Subcategory name') : __('Category name')"
          :aria-label="__('Name')"
          @keydown.enter="submit"
        />
      </div>

      <!-- Lines up with the name input, past the icon tile. -->
      <div
        class="mt-2 transition-[padding] duration-200 ease-out motion-reduce:transition-none"
        :class="drawn ? 'pl-20' : 'pl-10 delay-150'"
      >
        <Textarea
          v-model="description"
          class="resize-none"
          size="md"
          :rows="2"
          :placeholder="__('Add a short description')"
          :aria-label="__('Description')"
        />
      </div>
    </template>

    <template #actions>
      <div class="flex items-center justify-between gap-3">
        <p v-if="hasSubcategories" class="text-p-sm text-ink-gray-5">
          {{ __("Has subcategories, so it can't be nested.") }}
        </p>
        <!-- Waits for the options: they say whether it has subcategories. -->
        <Checkbox
          v-else
          :model-value="drawn"
          :disabled="categoryOptions.loading"
          :label="__('Add as a subcategory')"
          @update:model-value="$event ? nest() : unnest()"
        />
        <Button
          variant="solid"
          :label="actionLabel"
          :disabled="!canSave"
          @click="submit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import {
  Button,
  Checkbox,
  Combobox,
  Dialog,
  Textarea,
  TextInput,
  Tooltip,
} from "frappe-ui";
import { categoryOptions } from "@/stores/knowledgeBase";
import { categoryIcon } from "@helpdesk/shared/categoryIcons";
import { __ } from "@/translation";
import IconPicker from "@helpdesk/shared/IconPicker.vue";

const props = defineProps({
  edit: {
    type: Boolean,
    default: false,
  },
  // The category being edited, left out of the parent options.
  categoryId: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["update", "create"]);

const showDialog = defineModel<boolean>();
const newTitle = defineModel<string>("title");
const description = defineModel<string>("description");
const icon = defineModel<string>("icon");
const parent = defineModel<string>("parent", { default: "" });

// `nesting` holds the parent row; `drawn` holds its pieces, so they animate out first.
const nesting = ref(false);
const drawn = ref(false);
// Down from the tile's centre, a 6px elbow, then across to 4px short of the icon.
const ELBOW = "M0 0 V18 Q0 24 6 24 H20";

function nest() {
  nesting.value = true;
  drawn.value = true;
}

function unnest() {
  drawn.value = false;
}

// Also fires when a re-tick cuts the leave short.
function onUndrawn() {
  if (drawn.value) return;
  nesting.value = false;
  parent.value = "";
}

const nameInput = ref<InstanceType<typeof TextInput> | null>(null);

watch(showDialog, async (open) => {
  if (!open) return;
  // shared with other dialogs: drop their list before it shows here
  categoryOptions.reset();
  categoryOptions.submit();
  nesting.value = drawn.value = Boolean(parent.value);
  await nextTick();
  nameInput.value?.focus();
});

// The tile left of the picker shows the icon, so options stay text only.
const parentOptions = computed(() =>
  (categoryOptions.data || [])
    .filter(
      (option) =>
        !option.parent_article_category && option.value !== props.categoryId
    )
    .map(({ value, label }) => ({ value, label }))
);

const hasSubcategories = computed(
  () =>
    categoryOptions.data?.find((option) => option.value === props.categoryId)
      ?.has_subcategories
);

const parentIcon = computed(() =>
  categoryIcon(
    categoryOptions.data?.find((option) => option.value === parent.value)?.icon
  )
);

const dialogTitle = computed(() => {
  if (props.edit) return __("Edit category");
  return nesting.value ? __("New subcategory") : __("New category");
});

const actionLabel = computed(() => {
  if (props.edit) return __("Save changes");
  return nesting.value ? __("Create subcategory") : __("Create category");
});

// `drawn` is the intent; `nesting` lags it while the parent row animates out.
const canSave = computed(
  () => Boolean(newTitle.value?.trim()) && (!drawn.value || parent.value)
);

function submit() {
  if (!canSave.value) return;
  // a parent removed mid-animation is already gone
  if (!drawn.value) onUndrawn();
  emit(props.edit ? "update" : "create");
}
</script>
