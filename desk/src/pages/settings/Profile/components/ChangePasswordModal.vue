<template>
  <Dialog v-model="show" :options="{ title: __('Change Password') }">
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div>
          <Password v-model="newPassword" :placeholder="__('New Password')">
            <template #prefix>
              <LockKeyhole class="size-4 text-ink-gray-4" />
            </template>
          </Password>
          <p v-if="newPasswordMessage" class="text-sm text-ink-gray-5 mt-2">
            {{ newPasswordMessage }}
          </p>
        </div>
        <div>
          <Password
            v-model="confirmPassword"
            :placeholder="__('Confirm Password')"
          >
            <template #prefix>
              <LockKeyhole class="size-4 text-ink-gray-4" />
            </template>
          </Password>
          <p
            v-if="confirmPasswordMessage"
            class="text-sm text-ink-gray-5 mt-2"
            :class="
              confirmPasswordMessage === 'Passwords match'
                ? 'text-ink-green-3'
                : 'text-ink-red-3'
            "
          >
            {{ confirmPasswordMessage }}
          </p>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-between items-center">
        <div>
          <ErrorMessage :message="error" />
        </div>
        <Button
          variant="solid"
          :label="__('Update')"
          :disabled="
            !newPassword || !confirmPassword || newPassword !== confirmPassword
          "
          :loading="updatePassword.loading"
          @click="updatePassword.submit()"
        />
      </div>
    </template>
  </Dialog>
</template>
<script setup lang="ts">
import LockKeyhole from "~icons/lucide/lock-keyhole";
import { Dialog, toast, createResource } from "frappe-ui";
import { ref, watch } from "vue";
import { __ } from "@/translation";
import { useAuthStore } from "@/stores/auth";

const show = defineModel<boolean>();

const auth = useAuthStore();

const newPassword = ref("");
const confirmPassword = ref("");
const newPasswordMessage = ref("");
const confirmPasswordMessage = ref("");

const error = ref("");

const updatePassword = createResource({
  url: "frappe.client.set_value",
  makeParams() {
    return {
      doctype: "User",
      name: auth?.user,
      fieldname: "new_password",
      value: newPassword.value,
    };
  },
  onSuccess: () => {
    toast.success(__("Password updated successfully"));
    show.value = false;
    newPassword.value = "";
    confirmPassword.value = "";
    error.value = "";
  },
});

function isStrongPassword(password) {
  const regex =
    /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
  return regex.test(password);
}

watch([newPassword, confirmPassword], () => {
  confirmPasswordMessage.value = "";
  newPasswordMessage.value = "";

  if (newPassword.value.length < 8) {
    newPasswordMessage.value = __("Password must be at least 8 characters");
  } else if (!isStrongPassword(newPassword.value)) {
    newPasswordMessage.value = __(
      "Password must contain uppercase, lowercase, number, and symbol"
    );
  }

  if (
    confirmPassword.value.length &&
    newPassword.value !== confirmPassword.value
  ) {
    confirmPasswordMessage.value = __("Passwords do not match");
  } else if (
    newPassword.value === confirmPassword.value &&
    newPassword.value.length &&
    confirmPassword.value.length
  ) {
    confirmPasswordMessage.value = __("Passwords match");
  }
});
</script>
