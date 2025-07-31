<template>
  <Dialog
    v-model="show"
    :options="{
      title: 'Assign To',
      size: 'xl',
    }"
  >
    <template #body-content>
      <AutocompleteNew
        v-if="showRestrictedMembers"
        placeholder="Search agents"
        :model-value="search"
        :options="members"
        @update:model-value="
          ({ _, value }) => {
            addAssignee(value);
          }
        "
      >
        <template #item-prefix="{ option }">
          <UserAvatar class="mr-2" :name="option.value" size="sm" />
        </template>
        <template #item-label="{ option }">
          <Tooltip :text="option.value">
            {{ getUser(option.value).full_name }}
          </Tooltip>
        </template>
      </AutocompleteNew>

      <SearchComplete
        v-else
        class="form-control"
        doctype="HD Agent"
        :custom-filters="customFilters"
        :reset-input="true"
        @change="
          (option) => {
            addAssignee(option.value);
          }
        "
      >
        <template #item-prefix="{ option }">
          <UserAvatar class="mr-2" :name="option.value" size="sm" />
        </template>
        <template #item-label="{ option }">
          <Tooltip :text="option.value">
            {{ getUser(option.value).full_name }}
          </Tooltip>
        </template>
      </SearchComplete>

      <div class="mt-3 flex flex-wrap items-center gap-2">
        <Tooltip
          v-for="currentAssignee in assignees"
          :key="currentAssignee.name"
          :text="currentAssignee.name"
        >
          <Button
            :label="getUser(currentAssignee.name).full_name"
            theme="gray"
            variant="outline"
          >
            <template #prefix>
              <UserAvatar :name="currentAssignee.name" size="sm" />
            </template>
            <template #suffix>
              <FeatherIcon
                class="h-3.5"
                name="x"
                @click.stop="removeCurrentAssignee(currentAssignee.name)"
              />
            </template>
          </Button>
        </Tooltip>
      </div>
      <ErrorMessage v-if="error" class="mt-2" :message="error" />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { AutocompleteNew, SearchComplete, UserAvatar } from "@/components";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { useUserStore } from "@/stores/user";
import { call, createResource } from "frappe-ui";
import { useOnboarding } from "frappe-ui/frappe";
import { computed, onMounted, ref, watch } from "vue";

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  docname: {
    type: String,
    required: true,
  },
  assignees: {
    type: Array,
    required: true,
  },
  team: {
    type: String,
    default: "",
  },
});

const show = defineModel();

const emit = defineEmits(["update"]);

const { getUser } = useUserStore();
const { updateOnboardingStep } = useOnboarding("helpdesk");
const { isManager } = useAuthStore();
const { teamRestrictionApplied, assignWithinTeam } = useConfigStore();

const error = ref("");

const addAssignee = (value) => {
  error.value = "";
  createResource({
    url: "frappe.desk.form.assign_to.add",
    auto: true,
    params: {
      doctype: props.doctype,
      name: props.docname,
      assign_to: [value],
    },
    onSuccess: () => {
      emit("update");
      if (isManager) {
        updateOnboardingStep("assign_to_agent");
      }
      members.value = members.value.filter((m) => m.value !== value);
    },
  });
  emit("update");
};

const removeCurrentAssignee = (value) => {
  createResource({
    url: "frappe.desk.form.assign_to.remove",
    auto: true,
    params: {
      doctype: props.doctype,
      name: props.docname,
      assign_to: value,
    },
    onSuccess: () => {
      emit("update");
      members.value.push({
        label: value,
        value: value,
      });
    },
  });
};

const customFilters = computed(() => {
  const filters = {};
  filters["is_active"] = ["=", 1];
  if (Boolean(props.assignees?.length)) {
    filters["name"] = ["not in", [...props.assignees.map((a) => a.name)]];
  }
  return filters;
});

const search = ref("");
const members = ref([]);
async function getMembers() {
  let teamMembers = await call(
    "helpdesk.helpdesk.doctype.hd_team.hd_team.get_team_members",
    {
      team: props.team,
    }
  );
  let assignedMembers = props.assignees.map((a) => a.name);
  teamMembers = teamMembers.filter((member: string) => {
    return !assignedMembers.includes(member);
  });

  members.value = teamMembers.map((member: string) => {
    return {
      label: member,
      value: member,
    };
  });
}

const showRestrictedMembers = computed(() => {
  return teamRestrictionApplied && assignWithinTeam && props.team;
});

onMounted(() => {
  if (showRestrictedMembers.value) {
    getMembers();
  }
});
</script>
