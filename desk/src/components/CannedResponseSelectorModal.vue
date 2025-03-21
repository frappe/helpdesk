<template>
  <Dialog
    v-model="show"
    :options="{
      title: 'Canned Responses',
      size: '4xl',
    }"
  >
    <template #body-content>
      <TextInput
        ref="searchInput"
        v-model="search"
        type="text"
        :placeholder="'Site Down'"
      >
        <template #prefix>
          <FeatherIcon name="search" class="h-4 w-4 text-gray-500" />
        </template>
      </TextInput>
      <div
        v-if="filteredTemplates.length"
        class="mt-2 grid max-h-[560px] grid-cols-1 md:grid-cols-3 gap-2 overflow-y-auto"
      >
        <div
          v-for="template in filteredTemplates"
          :key="template.name"
          class="flex h-56 cursor-pointer flex-col gap-2 rounded-lg border p-3 hover:bg-gray-100"
          @click="emit('apply', template)"
        >
          <div class="border-b pb-2 text-base font-semibold">
            {{ template.title }}
          </div>
          <TextEditor
            v-if="template.message"
            :content="template.message"
            :editable="false"
            editor-class="!prose-sm max-w-none !text-sm text-gray-600 focus:outline-none"
            class="flex-1 overflow-hidden"
          />
        </div>
      </div>
      <div v-else class="mt-2">
        <div class="flex h-56 flex-col items-center justify-center">
          <div class="text-lg text-gray-500">
            {{ "No templates found" }}
          </div>
        </div>
      </div>
      <div class="flex justify-end mt-4">
        <Button
          label="New Canned Response"
          @click="
            () => {
              $router.push('/canned-responses#new');
              templates.data = null;
            }
          "
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { TextEditor, createListResource } from "frappe-ui";
import { ref, computed, nextTick, watch, onMounted } from "vue";

const props = defineProps({
  doctype: {
    type: String,
    default: "",
  },
});

const show = defineModel();
const searchInput = ref("");

const emit = defineEmits(["apply"]);

const search = ref("");

const templates = createListResource({
  type: "list",
  doctype: "HD Canned Response",
  cache: ["cannedResponses", props.doctype],
  fields: ["title", "message", "modified"],
  orderBy: "modified desc",
  pageLength: 99999,
});

onMounted(() => {
  if (templates.data == null) {
    templates.fetch();
  }
});

const filteredTemplates = computed(() => {
  return (
    templates.data?.filter((template) => {
      return template.title.toLowerCase().includes(search.value.toLowerCase());
    }) ?? []
  );
});

watch(show, (value) => value && nextTick(() => searchInput.value?.el?.focus()));
</script>
