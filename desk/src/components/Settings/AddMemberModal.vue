<template>
  <Dialog v-model="show" :options="{ title: 'Add members' }">
    <template #body-content>
      <div class="space-y-4">
        <FormControl type="text" v-model="query" placeholder="Search agents" />
        <div v-if="agents.data.length === 0">
          <p class="text-base text-gray-600">
            No agents found, please add
            <span
              class="cursor-pointer underline"
              @click="console.log('agents add')"
              >agents</span
            >
            in the system.
          </p>
        </div>
        <div v-else class="flex flex-col gap-4">
          <div class="flex flex-col gap-2">
            <div
              v-for="agent in agents.data"
              :key="agent.name"
              class="flex items-center justify-between"
            >
              <div class="flex items-center gap-2">
                <Avatar :label="agent.agent_name" :image="agent.user_image" />
                <div class="text-base">
                  {{ agent.agent_name }}
                </div>
              </div>
              <Button
                label="Add"
                theme="gray"
                variant="outline"
                @click="addMember(agent.name)"
              />
            </div>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import Avatar from "frappe-ui/src/components/Avatar.vue";
import Dialog from "frappe-ui/src/components/Dialog.vue";
import { ref } from "vue";
import { useAgents } from "./agents";
const props = defineProps({
  team: {
    type: Object,
    required: true,
  },
});

const show = defineModel<boolean>();

const query = ref("");

const { agents } = useAgents(query);

function addMember(user: string) {
  const users = props.team.doc.users.concat([{ user }]);
  props.team.setValue.submit({
    users,
  });
}
</script>

<style scoped></style>
