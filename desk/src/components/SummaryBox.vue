<template>
  <div class="flex-1 flex-col text-base">
    <!-- Summary Block Header -->
    <div class="mb-1.5 ml-0.5 flex items-center justify-between">
      <div class="flex items-center gap-2 text-ink-gray-7">
        <Avatar
          size="md"
          :label="activity.summarizer"
          :image="getUser(activity.summarizedBy).user_image"
        />
        <p class="text-p-sm">
          <span class="font-medium text-ink-gray-9">
            {{ activity.summarizer }}
          </span>
          <span> generated a summary</span>
        </p>
      </div>

      <Tooltip :text="dateFormat(activity.creation, dateTooltipFormat)">
        <span class="pl-0.5 text-sm text-ink-gray-6">
          {{ timeAgo(activity.creation) }}
        </span>
      </Tooltip>
    </div>

    <div
      class="rounded-2xl border border-outline-gray-2 bg-surface-white px-5 py-5 shadow-sm transition-colors"
    >
      <div
        class="text-p-base text-ink-gray-8"
        title="Summary snippet"
        v-html="activity.snippet"
      ></div>

      <div class="mt-4 grid grid-cols-[1fr_auto_1fr] items-center gap-3">
        <span
          v-if="firstDetailPreview && previewVisible"
          class="fade-text text-start text-p-sm font-medium text-ink-gray-5"
        >
          {{ firstDetailPreview }}
        </span>
        <span v-else></span>

        <Button
          variant="subtle"
          class="justify-self-center text-ink-gray-7"
          :icon-right="show ? 'chevron-up' : 'chevron-down'"
          @click="toggleDetails"
        >
          {{ show ? __("See less") : __("See more") }}
        </Button>

        <span></span>
      </div>

      <div
        ref="detailsWrapper"
        class="details-wrapper"
        :class="{ 'details-wrapper--open': show }"
        :style="{ '--details-height': `${detailsHeight}px` }"
      >
        <div ref="detailsContent" class="pt-5">
          <div class="mb-4 border-t border-outline-gray-modals"></div>
          <TextEditor
            :editor-class="[
              'prose-f shrink text-p-sm transition-all duration-300 ease-in-out block w-full content',
              getFontFamily(activity.content),
            ]"
            :content="activity.content"
            :editable="false"
            :bubble-menu="[]"
            @change="() => {}"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useUserStore } from "@/stores/user";
import { SummaryActivity } from "@/types";
import { dateFormat, dateTooltipFormat, getFontFamily, timeAgo } from "@/utils";
import { Avatar, Button, TextEditor, Tooltip } from "frappe-ui";
import {
  PropType,
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from "vue";

const props = defineProps({
  activity: {
    type: Object as PropType<SummaryActivity>,
    required: true,
  },
});

const show = ref(false);
const previewVisible = ref(true);

const { getUser } = useUserStore();

const detailsWrapper = ref<HTMLElement | null>(null);
const detailsContent = ref<HTMLElement | null>(null);
const detailsHeight = ref(0);
let collapseTimeout: number | undefined;

const truncateText = (input: string, wordLimit = 18) => {
  const words = input.split(/\s+/);
  if (words.length <= wordLimit) {
    return input;
  }
  return `${words.slice(0, wordLimit).join(" ")}…`;
};

const firstDetailPreview = computed(() => {
  const content = props.activity?.content || "";
  if (!content || typeof window === "undefined") {
    return "";
  }

  try {
    const parser = new DOMParser();
    const doc = parser.parseFromString(content, "text/html");
    const heading = doc.querySelector("h1, h2, h3, h4, h5, h6");
    const firstElement = heading ?? doc.body.firstElementChild;
    const text = firstElement?.textContent?.trim();
    return text ? truncateText(text) : "";
  } catch (error) {
    console.error("Unable to parse summary content", error);
    return "";
  }
});

const toggleDetails = () => {
  show.value = !show.value;
};

const onCollapseTransitionEnd = (event: TransitionEvent) => {
  if (event.propertyName !== "max-height" || show.value) {
    return;
  }
  previewVisible.value = true;
  if (collapseTimeout !== undefined) {
    window.clearTimeout(collapseTimeout);
    collapseTimeout = undefined;
  }
};

const measureDetailsHeight = () => {
  if (!detailsContent.value) {
    return;
  }
  detailsHeight.value = detailsContent.value.offsetHeight;
};

const scheduleMeasure = () => {
  nextTick(() => {
    measureDetailsHeight();
  });
};

onMounted(() => {
  scheduleMeasure();
  previewVisible.value = !show.value;
  window.addEventListener("resize", scheduleMeasure, { passive: true });
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", scheduleMeasure);
  if (collapseTimeout !== undefined) {
    window.clearTimeout(collapseTimeout);
  }
});

watch(
  () => show.value,
  (expanded) => {
    if (collapseTimeout !== undefined) {
      window.clearTimeout(collapseTimeout);
      collapseTimeout = undefined;
    }

    previewVisible.value = false;
    scheduleMeasure();

    if (expanded) {
      return;
    }

    const wrapper = detailsWrapper.value;
    if (!wrapper) {
      previewVisible.value = true;
      return;
    }

    wrapper.addEventListener("transitionend", onCollapseTransitionEnd, {
      once: true,
    });

    collapseTimeout = window.setTimeout(() => {
      if (!show.value) {
        previewVisible.value = true;
      }
      collapseTimeout = undefined;
    }, 420);
  }
);

watch(
  () => props.activity.content,
  () => {
    scheduleMeasure();
  }
);
</script>

<style scoped>
.fade-text {
  position: relative;
  display: block;
  max-width: 100%;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.details-wrapper {
  max-height: 0;
  opacity: 0;
  transform: translateY(-6px);
  overflow: hidden;
  transition: max-height 0.32s ease, opacity 0.24s ease, transform 0.32s ease;
}

.details-wrapper--open {
  max-height: var(--details-height, 600px);
  opacity: 1;
  transform: translateY(0);
}

.fade-text::after {
  content: "";
  position: absolute;
  top: 0;
  right: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  background: linear-gradient(
    to right,
    rgba(255, 255, 255, 0) 0%,
    rgba(255, 255, 255, 1) 100%
  );
}
</style>
