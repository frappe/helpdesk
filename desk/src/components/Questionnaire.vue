<template>
  <div class="relative mx-auto w-full max-w-md flex flex-col gap-5">
    <HDLogo class="size-8" />

    <!-- Fixed height keeps the panel from resizing as questions vary in length. -->
    <div>
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
            Answer a few quick questions so we can tailor Helpdesk to how you
            work.
          </p>
          <div class="flex flex-wrap gap-3 mt-5 !text-ink-gray-7 text-p-base">
            <Button
              v-for="option in question.options"
              :key="option.value"
              :label="option.label"
              :variant="
                isSelected(option)
                  ? 'subtle'
                  : 'outline active:bg-surface-gray-4 border-solid active:!border-outline-gray-3'
              "
              :icon-right="
                question.multiple && isSelected(option) ? 'lucide-x' : undefined
              "
              size="md"
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
import { Button } from "frappe-ui";
import { computed, reactive, ref } from "vue";

interface Option {
  label: string;
  value: string;
}
interface Question {
  key: string;
  title: string;
  options: Option[];
  multiple?: boolean;
}

type Answers = Record<string, string | string[]>;

const props = defineProps<{ questions: Question[] }>();
const emit = defineEmits<{ submit: [answers: Answers] }>();

const current = ref(0);
const completed = ref(false);
const answers = reactive<Answers>({});

const total = computed(() => props.questions.length);
const question = computed(() => props.questions[current.value] as Question);
const isLast = computed(() => current.value === total.value - 1);

function isSelected(option: Option) {
  const value = answers[question.value.key];
  if (question.value.multiple) {
    return Array.isArray(value) && value.includes(option.value);
  }
  return value === option.value;
}

function select(option: Option) {
  if (completed.value) return;
  const key = question.value.key;
  if (question.value.multiple) {
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
