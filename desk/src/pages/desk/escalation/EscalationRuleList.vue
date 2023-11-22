<template>
  <div class="flex flex-col">
    <PageTitle title="Escalation Rules">
      <template #right>
        <Button
          label="New rule"
          theme="gray"
          variant="solid"
          @click="openDialog(null)"
        >
          <template #prefix>
            <LucidePlus class="h-4 w-4" />
          </template>
        </Button>
      </template>
    </PageTitle>
    <ListView :resource="rules" class="mt-2.5" doctype="HD Escalation Rule">
      <template #is_enabled="{ data }">
        <Badge :theme="data.is_enabled ? 'green' : 'red'" variant="subtle">
          {{ data.is_enabled ? 'Enabled' : 'Disabled' }}
        </Badge>
      </template>
    </ListView>
    <EscalationRuleDialog
      v-if="showDialog"
      v-model="showDialog"
      :name="selectedRule"
    />
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue';
import { usePageMeta, Badge } from 'frappe-ui';
import { socket } from '@/socket';
import { createListManager } from '@/composables/listManager';
import { ListView } from '@/components';
import PageTitle from '@/components/PageTitle.vue';
import EscalationRuleDialog from './EscalationRuleDialog.vue';

const showDialog = ref(false);
const selectedRule = ref(null);

const rules = createListManager({
  doctype: 'HD Escalation Rule',
  fields: ['name', 'priority', 'team', 'ticket_type', 'is_enabled'],
  auto: true,
  transform: (data) => {
    for (const d of data) {
      d.onClick = () => openDialog(d.name);
    }
    return data;
  },
});

usePageMeta(() => {
  return {
    title: 'Escalation rules',
  };
});

function openDialog(rule: string | null) {
  selectedRule.value = rule;
  showDialog.value = true;
}

socket.on('helpdesk:new-escalation-rule', () => rules.reload());
socket.on('helpdesk:delete-escalation-rule', () => rules.reload());
</script>
