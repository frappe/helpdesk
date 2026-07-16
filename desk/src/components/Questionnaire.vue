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
      <div
        :key="question.key"
        class="mx-0 min-w-0 border-0 p-0 flex gap-5 flex-col"
      >
        <div>
          <p class="p-0 text-p-2xl font-bold text-ink-gray-9">
            {{ question.title }}
          </p>

          <p class="text-base pt-1.5">
            A few quick questions to tailor Helpdesk to how you work.
          </p>
        </div>
        <template v-if="question.type === 'text'">
          <div class="flex flex-col gap-3">
            <div>
              <span
                v-if="question.label"
                class="mb-1.5 block text-p-sm text-ink-gray-5"
              >
                {{ question.label
                }}<span v-if="question.required" class="ms-0.5 text-ink-red-6"
                  >*</span
                >
              </span>
              <Textarea
                v-if="question.multiline"
                v-model="answers[question.key]"
                size="sm"
                variant="outline"
                :rows="3"
                :placeholder="question.placeholder"
              />
              <TextInput
                v-else
                v-model="answers[question.key]"
                size="sm"
                type="text"
                variant="outline"
                :placeholder="question.placeholder"
                @keyup.enter="proceed"
              />
            </div>
            <div v-if="dropdown">
              <span class="mb-1.5 block text-p-sm text-ink-gray-5">
                {{ dropdown.label }}
              </span>
              <Select
                v-model="answers[dropdown.key]"
                class="w-full"
                size="sm"
                variant="outline"
                :placeholder="dropdown.placeholder"
                :options="dropdown.options"
              />
            </div>
          </div>
        </template>
        <template v-else>
          <div class="flex flex-wrap gap-3 !text-ink-gray-7 text-p-base">
            <Button
              v-for="option in choiceOptions"
              :key="option.value"
              :label="option.label"
              :variant="isSelected(option) ? 'subtle' : 'outline'"
              size="sm"
              class="!rounded-md border border-solid"
              :class="
                isSelected(option)
                  ? '!bg-surface-gray-4 !border-outline-gray-3 hover:!bg-surface-gray-5'
                  : ''
              "
              @click="select(option)"
            />
          </div>
          <div
            class="-mt-5 grid transition-[grid-template-rows,opacity] duration-300 ease-[cubic-bezier(0.22,1,0.36,1)]"
            :class="
              isOtherSelected
                ? 'grid-rows-[1fr] opacity-100'
                : 'grid-rows-[0fr] opacity-0'
            "
          >
            <div class="overflow-hidden">
              <div
                class="transition-transform duration-300 ease-[cubic-bezier(0.22,1,0.36,1)]"
                :class="isOtherSelected ? 'translate-y-0' : '-translate-y-full'"
              >
                <Textarea
                  ref="otherInput"
                  v-model="answers[otherKey]"
                  class="mt-5"
                  variant="outline"
                  :rows="3"
                  :placeholder="__('Please specify')"
                  :tabindex="isOtherSelected ? 0 : -1"
                />
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <div class="flex flex-col items-center gap-2">
      <Button
        class="!h-7 w-full !rounded-lg"
        variant="solid"
        :label="isLast ? __('Finish') : __('Next')"
        :disabled="!canProceed"
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
import { Button, Select, Textarea, TextInput } from "frappe-ui";
import { computed, nextTick, reactive, ref } from "vue";
import type { Option, Question } from "./Questionnaire.types";

type Answers = Record<string, string | string[]>;

const props = defineProps<{ questions: Question[] }>();
const emit = defineEmits<{ submit: [answers: Answers] }>();

const current = ref(0);
const completed = ref(false);
const answers = reactive<Answers>({});
const otherInput = ref<InstanceType<typeof Textarea>>();

const total = computed(() => props.questions.length);
const question = computed(() => props.questions[current.value] as Question);
const isLast = computed(() => current.value === total.value - 1);

// Next stays disabled until the current question has an answer.
const canProceed = computed(() => {
  const q = question.value;
  const value = answers[q.key];
  if (q.type === "text")
    return !q.required || (typeof value === "string" && value.trim() !== "");
  if (q.multiple) return Array.isArray(value) && value.length > 0;
  return typeof value === "string" && value !== "";
});

// Narrow the discriminated union so the template stays declarative: choice
// questions render pills, text questions may carry a dropdown beneath them.
const choiceOptions = computed(() =>
  question.value.type === "choice" ? question.value.options : []
);
const dropdown = computed(() =>
  question.value.type === "text" ? question.value.dropdown : undefined
);

// "Other" free-text is stored under a `<key>_other` sibling answer key.
const OTHER_SUFFIX = "_other";
const otherKey = computed(() => `${question.value.key}${OTHER_SUFFIX}`);
const isOtherSelected = computed(() => {
  const otherOption = choiceOptions.value.find((o) => o.value === "other");
  return otherOption ? isSelected(otherOption) : false;
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
  } else {
    // A click only sets the selection; advancing is always via the Next button.
    answers[key] = option.value;
  }

  if (!isOtherSelected.value) {
    delete answers[otherKey.value];
  } else if (option.value === "other") {
    nextTick(() => otherInput.value?.el?.focus({ preventScroll: true }));
  }
}

function advance() {
  if (current.value < total.value - 1) current.value += 1;
}

function back() {
  if (current.value > 0) current.value -= 1;
}

function proceed() {
  if (!canProceed.value) return;
  if (isLast.value) finish();
  else advance();
}

function finish() {
  if (completed.value) return;
  completed.value = true;
  setTimeout(() => emit("submit", { ...answers }), 700);
}
</script>
