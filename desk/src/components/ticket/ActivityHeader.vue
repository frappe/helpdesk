<template>
  <div
    class="md:mx-10 md:my-4 flex items-center justify-between text-lg font-medium mx-6 mb-4 !mt-8"
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
import { CommentIcon, EmailIcon } from "@/components/icons";
import { Dropdown } from "frappe-ui";
import { computed, h, inject, Ref } from "vue";
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
      label: "Email",
      onClick: () => communicationAreaRef.value.toggleEmailBox(),
    },
    {
      icon: h(CommentIcon, { class: "h-4 w-4" }),
      label: "Comment",
      onClick: () => communicationAreaRef.value.toggleCommentBox(),
    },
  ];
  return actions;
});
</script>

<style scoped></style>
