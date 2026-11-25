<template>
  <section class="flex flex-col gap-4">
    <div class="flex items-start justify-between gap-4">
      <div class="flex min-w-0 flex-col gap-1">
        <span class="text-base-semibold text-ink-gray-9">
          {{ __("Skills") }}
        </span>
        <span class="text-p-sm text-ink-gray-6">
          {{
            __(
              "Instructions the assistant follows on every answer, such as tone or what to mention."
            )
          }}
        </span>
      </div>
      <Button
        class="shrink-0"
        :label="__('Add skill')"
        icon-left="lucide-plus"
        @click="showAdd = true"
      />
    </div>

    <div
      v-if="skills.data?.length"
      class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-1"
    >
      <div
        v-for="skill in skills.data"
        :key="skill.name"
        class="flex items-center gap-3 px-4 py-3"
      >
        <div class="flex min-w-0 flex-1 flex-col gap-0.5">
          <span class="truncate text-base-medium text-ink-gray-8">
            {{ skill.name }}
          </span>
          <span
            class="truncate text-p-sm text-ink-gray-5"
            :title="skill.instructions"
          >
            {{ skill.instructions }}
          </span>
        </div>
        <Tooltip :text="__('Remove skill')">
          <Button
            variant="ghost"
            icon="lucide-trash-2"
            :aria-label="__('Remove skill')"
            :loading="remove.loading && remove.params?.title === skill.name"
            @click="remove.submit({ title: skill.name })"
          />
        </Tooltip>
      </div>
    </div>
    <p v-else-if="skills.data" class="text-p-sm text-ink-gray-5">
      {{ __("No skills yet.") }}
    </p>

    <Dialog
      v-model:open="showAdd"
      :title="__('Add skill')"
      :actions="[
        {
          label: __('Add skill'),
          variant: 'solid',
          onClick: () => add.submit(),
        },
      ]"
    >
      <div class="flex flex-col gap-4">
        <FormControl
          v-model="form.title"
          :label="__('Name')"
          :placeholder="__('Friendly tone')"
          required
        />
        <FormControl
          v-model="form.instructions"
          type="textarea"
          :label="__('Instructions')"
          :placeholder="__('Answer in short, friendly sentences.')"
          required
        />
        <ErrorMessage :message="add.error?.messages?.[0]" />
      </div>
    </Dialog>
  </section>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import {
  Button,
  createResource,
  Dialog,
  ErrorMessage,
  FormControl,
  toast,
  Tooltip,
} from "frappe-ui";
import { reactive, ref, watch } from "vue";

const API = "helpdesk.api.ai_search";

const skills = createResource({ url: `${API}.get_skills`, auto: true });

const showAdd = ref(false);
const form = reactive({ title: "", instructions: "" });
watch(showAdd, (open) => {
  if (!open) return;
  Object.assign(form, { title: "", instructions: "" });
  add.reset();
});

const add = createResource({
  url: `${API}.add_skill`,
  makeParams: () => ({ ...form }),
  onSuccess() {
    showAdd.value = false;
    skills.reload();
    toast.success(__("Skill added"));
  },
});

const remove = createResource({
  url: `${API}.remove_skill`,
  onSuccess: () => skills.reload(),
  onError(error: { messages?: string[] }) {
    toast.error(error.messages?.[0] || __("Could not remove the skill"));
  },
});
</script>
