<template>
  <div
    class="relative mx-auto w-full max-w-2xl rounded-2xl bg-surface-white p-4"
  >
    <div class="flex flex-col">
      <HDLogo class="size-8" />
      <Transition name="q-fade" mode="out-in" @after-enter="focusQuestion">
        <fieldset
          :key="question.key"
          tabindex="-1"
          class="mt-6 mx-0 min-w-0 border-0 p-0 focus:outline-none"
        >
          <legend class="p-0 text-xl font-semibold text-ink-gray-9">
            {{ question.title }}
          </legend>
          <p class="mt-1 h-5 text-sm text-ink-gray-5">
            {{ question.multiple ? __("Select all that apply") : "" }}
          </p>
          <div class="mt-5 flex flex-wrap gap-2.5">
            <Button
              v-for="option in question.options"
              :key="option.value"
              :label="option.label"
              variant="outline"
              size="md"
              class="!rounded-full bg-surface-gray-1 hover:bg-surface-gray-3"
              :class="
                isSelected(option) ? '!bg-surface-gray-9 !text-ink-white' : ''
              "
              @click="select(option)"
            />
          </div>
        </fieldset>
      </Transition>
    </div>

    <div class="mt-6 flex items-center justify-between">
      <div class="text-sm font-medium text-ink-gray-5">
        {{ __("Step {0} of {1}", String(current + 1), String(total)) }}
      </div>

      <div class="flex items-center gap-2">
        <Button
          :disabled="current < 1"
          variant="subtle"
          :label="__('Previous')"
          icon-left="lucide-arrow-left"
          @click="back"
        />
        <Button
          v-if="current < total - 1"
          variant="solid"
          :disabled="!answered"
          icon-right="lucide-arrow-right"
          :label="__('Next')"
          @click="next"
        />
        <Button
          v-else
          :disabled="!answered"
          variant="solid"
          :label="__('Finish')"
          @click="finish"
        />
      </div>
    </div>
  </div>
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

const answered = computed(() => {
  const value = answers[question.value.key];
  if (question.value.multiple) return Array.isArray(value) && value.length > 0;
  return value !== undefined;
});

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
  // Single-select auto-advances; multi-select returned above and waits for Next.
  answers[key] = option.value;
  if (current.value < total.value - 1) advance();
}

function advance() {
  if (current.value < total.value - 1) current.value += 1;
}

function next() {
  if (answered.value) advance();
}

function back() {
  if (current.value > 0) current.value -= 1;
}

function finish() {
  if (!answered.value || completed.value) return;
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
