<template>
  <div class="divide-y rounded-t-xl border-b">
    <div class="px-3.5 py-1.5 text-base">
      <div class="flex justify-between">
        <div class="flex items-center gap-4">
          <div class="w-6 text-gray-600">To:</div>
          <UserBubble :name="to" />
        </div>
        <div class="flex gap-2">
          <div
            class="flex cursor-pointer items-center justify-center rounded-md px-2 py-1 text-base text-gray-800"
            :class="{
              'bg-gray-300': editor.isCcVisible,
            }"
            @click="editor.isCcVisible = !editor.isCcVisible"
          >
            Cc
          </div>
          <div
            class="flex cursor-pointer items-center justify-center rounded-md px-2 py-1 text-base text-gray-800"
            :class="{
              'bg-gray-300': editor.isBccVisible,
            }"
            @click="editor.isBccVisible = !editor.isBccVisible"
          >
            Bcc
          </div>
        </div>
      </div>
    </div>
    <div v-if="editor.isCcVisible" class="px-3.5 py-1.5 text-base">
      <div class="flex items-center gap-4">
        <div class="w-6 text-gray-600">Cc:</div>
        <div class="flex w-full flex-wrap gap-1">
          <UserBubble
            v-for="cc in editor.cc"
            :key="cc"
            :name="cc"
            class="cursor-pointer hover:bg-red-300"
            @click="() => removeFromArray(editor.cc, cc)"
          />
          <Input
            class="min-w-min grow bg-white text-gray-800 focus:bg-white"
            @keyup.enter="(v) => addToArray(editor.cc, v)"
            @keyup.space="(v) => addToArray(editor.cc, v)"
          />
        </div>
      </div>
    </div>
    <div v-if="editor.isBccVisible" class="px-3.5 py-1.5 text-base">
      <div class="flex items-center gap-4">
        <div class="w-6 text-gray-600">Bcc:</div>
        <div class="flex w-full flex-wrap gap-1">
          <UserBubble
            v-for="bcc in editor.bcc"
            :key="bcc"
            :name="bcc"
            class="cursor-pointer hover:bg-red-300"
            @click="() => removeFromArray(editor.bcc, bcc)"
          />
          <Input
            class="min-w-min grow bg-white text-gray-800 focus:bg-white"
            @keyup.enter="(v) => addToArray(editor.bcc, v)"
            @keyup.space="(v) => addToArray(editor.bcc, v)"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useTicketStore } from "../data";
import UserBubble from "./UserBubble.vue";

const { editor, ticket } = useTicketStore();
const to = computed(() => ticket.doc.raised_by);

function addToArray(array: Array<string>, el) {
  const value = el.target.value;
  if (array.indexOf(value) < 0) array.push(value);
  el.target.value = "";
}

function removeFromArray(array: Array<string>, item: string) {
  array.splice(array.indexOf(item), 1);
}
</script>
