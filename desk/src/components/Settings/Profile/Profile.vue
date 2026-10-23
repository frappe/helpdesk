<template>
  <SettingsLayoutBase
    :title="__('Profile')"
    :description="__('Manage your profile information.')"
  >
    <template #content>
      <div class="flex items-center justify-between gap-2 pt-1.5 pb-8">
        <AvatarRow
          :image="user.doc?.user_image"
          :name="user.doc?.full_name"
          :subtitle="user.doc?.email"
          :busy="user.save.loading"
          @upload="updateImage"
          @remove="updateImage()"
          @rename="updateFullName"
        >
          <template #badge>
            <div
              v-if="agentStatusStore.myStatus"
              class="absolute -bottom-0.5 end-0 rounded-full bg-surface-elevation-2 p-1"
            >
              <div
                class="size-3.5 rounded-full"
                :class="agentStatusStore.statusColor(agentStatusStore.myStatus)"
              />
            </div>
          </template>
        </AvatarRow>
      </div>
      <div>
        <div class="flex items-center justify-between h-7">
          <div class="flex gap-2 items-center">
            <span class="text-base-semibold text-ink-gray-9">
              {{ __("Account Info & Security") }}
            </span>
          </div>
        </div>
      </div>

      <div v-if="hasAgentRecord" class="flex items-center justify-between mt-6">
        <div class="flex flex-col gap-1">
          <span class="text-base-medium text-ink-gray-8">
            {{ __("Availability") }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{
              __(
                "Set your availability so your team knows when you're reachable."
              )
            }}
          </span>
        </div>
        <AvailabilityMenu />
      </div>
      <div class="flex items-center justify-between mt-6">
        <div class="flex flex-col gap-1">
          <span class="text-base-medium text-ink-gray-8">
            {{ __("Emails & Signature") }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{
              __(
                "Manage your account emails and email signature for communication."
              )
            }}
          </span>
        </div>
        <Button
          :label="__('Configure')"
          @click="emit('updateStep', 'user-email-settings')"
        />
      </div>
      <div class="flex items-center justify-between mt-6">
        <div class="flex flex-col gap-1">
          <span class="text-base-medium text-ink-gray-8">
            {{ __("Password") }}
          </span>
          <span class="text-p-sm text-ink-gray-6">{{
            __("Change your account password for security.")
          }}</span>
        </div>
        <Button
          icon-left="lucide-lock"
          :label="__('Change Password')"
          @click="showChangePasswordModal = true"
        />
      </div>
    </template>
  </SettingsLayoutBase>
  <ChangePasswordModal
    v-if="showChangePasswordModal"
    v-model="showChangePasswordModal"
    :user="userId"
  />
</template>

<script setup lang="ts">
import { Button, createDocumentResource, toast } from "frappe-ui";
import { ref } from "vue";

import { useAuthStore } from "@/stores/auth";
import { __ } from "@/translation";
const emit = defineEmits(["updateStep"]);

import AvailabilityMenu from "@/components/AvailabilityMenu.vue";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { useAgentStatusStore } from "@/stores/agentStatus";
import AvatarRow from "@helpdesk/shared/AvatarRow.vue";
import ChangePasswordModal from "@helpdesk/shared/ChangePasswordModal.vue";

const agentStatusStore = useAgentStatusStore();
const showChangePasswordModal = ref(false);

const { userId, hasAgentRecord } = useAuthStore();
const user = createDocumentResource({ doctype: "User", name: userId });

function updateFullName(fullName: string) {
  const [firstName, ...lastName] = fullName.split(" ");
  user.doc.first_name = firstName;
  user.doc.last_name = lastName.join(" ");
  save();
}

function save() {
  user.save.submit(null, {
    onSuccess: () => {
      toast.success(__("Profile updated successfully."));
    },
    onError: (err: { message: string; messages: string[] }) => {
      toast.error(err.message + ": " + err.messages[0]);
    },
  });
}

function updateImage(fileUrl = "") {
  user.doc.user_image = fileUrl;
  save();
}
</script>
