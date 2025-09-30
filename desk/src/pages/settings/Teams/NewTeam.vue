<template>
  <SettingsHeader :routes="routes" />
  <div
    class="max-w-3xl xl:max-w-4xl mx-auto w-full px-4 relative flex flex-col-reverse pb-6"
  >
    <div class="flex flex-col gap-4">
      <FormControl
        v-model="newTeamTitle"
        label="Team Name"
        placeholder="Product Experts"
      />
      <div class="flex flex-col gap-1.5">
        <FormLabel label="Members" />
        <div class="p-1 group border rounded flex flex-1 bg-gray-100">
          <EmailMultiSelect
            class="flex-1"
            :placeholder="__('john@doe.com')"
            inputClass="!bg-white"
            itemClass="bg-white hover:bg-white"
            v-model="invitees"
            :validate="validateEmail"
            :error-message="
              (value) => __('{0} is an invalid email address', [value])
            "
            :emptyPlaceholder="__('Type an email address to invite')"
            :fetchUsers="true"
          />
        </div>
      </div>
    </div>
    <div
      class="flex items-center justify-between bg-white py-4 lg:py-8 sticky top-0"
    >
      <div class="flex items-center gap-1 justify-center">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          label="New Team"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-ink-gray-7 text-xl hover:opacity-70 !pr-0 max-w-48 md:max-w-60 lg:max-w-max overflow-ellipsis overflow-hidden"
          @click="router.push({ name: 'SettingsTeams' })"
        />
      </div>
      <Button
        label="Create"
        icon-left="plus"
        variant="solid"
        @click="newTeam.submit()"
        :loading="newTeam.loading"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import SettingsHeader from "../components/SettingsHeader.vue";
import { useRouter } from "vue-router";
import { createResource, FormControl, FormLabel, toast } from "frappe-ui";
import { validateEmail } from "@/utils";
import EmailMultiSelect from "@/components/EmailMultiSelect.vue";
import { __ } from "@/translation";

const router = useRouter();
const routes = computed(() => [
  {
    label: "Teams",
    route: "/settings/teams",
  },
  {
    label: "New Team",
    route: `/settings/teams/new`,
  },
]);
const invitees = ref<string[]>([]);
const newTeamTitle = ref(null);

const newTeam = createResource({
  url: "frappe.client.insert",
  makeParams() {
    return {
      doc: {
        doctype: "HD Team",
        team_name: newTeamTitle.value,
        users: invitees.value.map((email) => ({
          user: email,
        })),
      },
    };
  },
  validate(params) {
    if (!params.doc.team_name?.trim()) return "Title is required";
  },
  auto: false,
  onSuccess(data) {
    toast.success("Team created");
    newTeamTitle.value = null;
    invitees.value = [];
    router.push({ name: "EditSettingsTeam", params: { id: data.name } });
  },
});
</script>
