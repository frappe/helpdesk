<template>
  <div
    class="md:mx-10 md:my-8 flex items-center justify-between text-lg font-medium mx-5 mb-4 mt-8"
  >
    <div class="flex h-8 items-center text-xl font-semibold text-gray-800">
      {{ title }}
    </div>
    <Button
      v-if="title == 'Emails'"
      variant="solid"
      @click="communicationAreaRef.toggleEmailBox()"
    >
      <template #prefix>
        <FeatherIcon name="plus" class="h-4 w-4" />
      </template>
      <span>{{ "New Email" }}</span>
    </Button>
    <Button
      v-else-if="title == 'Comments'"
      variant="solid"
      @click="communicationAreaRef.toggleCommentBox()"
    >
      <template #prefix>
        <FeatherIcon name="plus" class="h-4 w-4" />
      </template>
      <span>{{ "New Comment" }}</span>
    </Button>
    <Dropdown v-else :options="defaultActions" @click.stop>
      <template v-slot="{ open }">
        <Button variant="solid" class="flex items-center gap-1">
          <template #prefix>
            <FeatherIcon name="plus" class="h-4 w-4" />
          </template>
          <span>{{ "New" }}</span>
          <template #suffix>
            <FeatherIcon
              :name="open ? 'chevron-up' : 'chevron-down'"
              class="h-4 w-4"
            />
          </template>
        </Button>
      </template>
    </Dropdown>
  </div>
</template>

<script setup lang="ts">
import { h } from "vue";
import { computed } from "vue";
import { EmailIcon, CommentIcon } from "@/components/icons";
import { Dropdown } from "frappe-ui";
import { inject } from "vue";
import { Ref } from "vue";
defineProps({
  title: {
    type: String,
    required: true,
  },
});

const communicationAreaRef: Ref = inject("communicationArea");

const defaultActions = computed(() => {
  let actions = [
    {
      icon: h(EmailIcon, { class: "h-4 w-4" }),
      label: "New Email",
      onClick: () => communicationAreaRef.value.toggleEmailBox(),
    },
    {
      icon: h(CommentIcon, { class: "h-4 w-4" }),
      label: "New Comment",
      onClick: () => communicationAreaRef.value.toggleCommentBox(),
    },
  ];
  return actions;
});
</script>

<style scoped></style>
