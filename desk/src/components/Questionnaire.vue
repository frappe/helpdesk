<template>
  <div class="relative mx-auto w-full max-w-md flex flex-col gap-5">
    <HDLogo class="size-8" />

    <!-- Fixed height keeps the panel from resizing as questions vary in length. -->
    <div class="relative">
      <Button
        v-if="current > 0"
        variant="ghost"
        icon="lucide-chevron-left"
        class="!size-7 shrink-0 !rounded-md absolute -left-11 mt-4"
        @click="back"
      />
      <Transition name="q-fade" mode="out-in" @after-enter="focusQuestion">
        <fieldset
          :key="question.key"
          tabindex="-1"
          class="mx-0 min-w-0 border-0 p-0 focus:outline-none"
        >
          <legend class="p-0 text-p-2xl font-bold text-ink-gray-9">
            {{ question.title }}
          </legend>

          <p class="text-p-base pt-1.5">
            A few quick questions to tailor Helpdesk to how you work.
          </p>
          <template v-if="question.type === 'text'">
            <div class="mt-5">
              <span
                v-if="question.label"
                class="mb-1.5 block text-p-sm text-ink-gray-5"
              >
                {{ question.label }}
              </span>
              <TextInput
                v-model="answers[question.key]"
                size="sm"
                type="text"
                variant="outline"
                :placeholder="question.placeholder"
                @keyup.enter="proceed"
              />
            </div>
            <div v-if="dropdown" class="mt-3">
              <span class="mb-1.5 block text-p-sm text-ink-gray-5">
                {{ dropdown.label }}
              </span>
              <Dropdown :options="dropdownOptions" match-trigger-width>
                <Button
                  class="w-full !justify-between !rounded-md"
                  size="sm"
                  variant="outline"
                  icon-right="lucide-chevron-down"
                  :label="dropdownLabel"
                  :aria-label="dropdown.label"
                  :class="dropdownSelected ? '' : '!text-ink-gray-5'"
                />
              </Dropdown>
            </div>
          </template>
          <div
            v-else
            class="flex flex-wrap gap-3 mt-5 !text-ink-gray-7 text-p-base"
          >
            <Button
              v-for="option in choiceOptions"
              :key="option.value"
              :label="option.label"
              :variant="
                isSelected(option)
                  ? 'subtle'
                  : 'outline active:bg-surface-gray-4 border-solid active:!border-outline-gray-3'
              "
              :icon-right="
                isMultiple && isSelected(option) ? 'lucide-x' : undefined
              "
              size="sm"
              class="!rounded-md border border-solid [&_[aria-hidden]]:!size-3"
              :class="
                isSelected(option)
                  ? '!bg-surface-gray-4 !border-outline-gray-3'
                  : '!border-outline-gray-2'
              "
              @click="select(option)"
            />
          </div>
        </fieldset>
      </Transition>
    </div>

    <div class="flex flex-col items-center gap-2">
      <Button
        class="!h-7 w-full !rounded-lg"
        variant="solid"
        :label="isLast ? __('Finish') : __('Next')"
        @click="proceed"
      />
    </div>
  </div>
  <Button
    class="mt-auto !bg-transparent !text-ink-gray-5 hover:!text-ink-gray-8"
    variant="ghost"
    :label="__('Skip for now')"
    @click="finish"
  />
</template>

<script setup lang="ts">
import HDLogo from "@/assets/logos/HDLogo.vue";
import { __ } from "@/translation";
import { Button, Dropdown, TextInput } from "frappe-ui";
import { computed, reactive, ref } from "vue";
import type { Option, Question } from "./Questionnaire.types";

type Answers = Record<string, string | string[]>;

const props = defineProps<{ questions: Question[] }>();
const emit = defineEmits<{ submit: [answers: Answers] }>();

const current = ref(0);
const completed = ref(false);
const answers = reactive<Answers>({});

const total = computed(() => props.questions.length);
const question = computed(() => props.questions[current.value] as Question);
const isLast = computed(() => current.value === total.value - 1);

// Narrow the discriminated union so the template stays declarative: choice
// questions render pills, text questions may carry a dropdown beneath them.
const choiceOptions = computed(() =>
  question.value.type === "choice" ? question.value.options : []
);
const isMultiple = computed(
  () => question.value.type === "choice" && !!question.value.multiple
);
const dropdown = computed(() =>
  question.value.type === "text" ? question.value.dropdown : undefined
);
// Dropdown menu items set the answer on click; the trigger reflects the choice.
const dropdownOptions = computed(() =>
  (dropdown.value?.options ?? []).map((option) => ({
    label: option.label,
    onClick: () => {
      if (dropdown.value) answers[dropdown.value.key] = option.value;
    },
  }))
);
const dropdownSelected = computed(
  () => !!dropdown.value && !!answers[dropdown.value.key]
);
const dropdownLabel = computed(() => {
  const config = dropdown.value;
  if (!config) return "";
  const value = answers[config.key];
  return (
    config.options.find((option) => option.value === value)?.label ??
    config.placeholder
  );
});

function isSelected(option: Option) {
  const q = question.value;
  if (q.type !== "choice") return false;
  const value = answers[q.key];
  if (q.multiple) {
    return Array.isArray(value) && value.includes(option.value);
  }
  return value === option.value;
}

function select(option: Option) {
  if (completed.value) return;
  const q = question.value;
  if (q.type !== "choice") return;
  const key = q.key;
  if (q.multiple) {
    const value = Array.isArray(answers[key])
      ? [...(answers[key] as string[])]
      : [];
    const index = value.indexOf(option.value);
    if (index === -1) {
      value.push(option.value);
    } else {
      value.splice(index, 1);
    }
    answers[key] = value;
    return;
  }
  // A click only sets the selection; advancing is always via the Next button.
  answers[key] = option.value;
}

function advance() {
  if (current.value < total.value - 1) current.value += 1;
}

function back() {
  if (current.value > 0) current.value -= 1;
}

// Next never blocks: an unanswered question is simply skipped past.
function proceed() {
  if (isLast.value) finish();
  else advance();
}

function finish() {
  if (completed.value) return;
  completed.value = true;
  setTimeout(() => emit("submit", { ...answers }), 700);
}

function focusQuestion(el: Element) {
  (el as HTMLElement).focus();
}
</script>

<style scoped>
.q-fade-enter-active,
.q-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.q-fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.q-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
