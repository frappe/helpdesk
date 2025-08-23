<template>
  <Dialog v-model="show" :options="{ title: __('Change Password') }">
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div>
          <Password v-model="newPassword" :placeholder="__('New Password')">
            <template #prefix>
              <FeatherIcon name="lock" class="size-4 text-ink-gray-4" />
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
              <FeatherIcon name="lock" class="size-4 text-ink-gray-4" />
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
<script setup>
import Password from "./Settings/Password.vue";
import { useAuthStore } from "@/stores/auth";
import { Dialog, toast, createResource } from "frappe-ui";
import { ref, watch } from "vue";

const { user } = useAuthStore();
const show = ref(false);
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
      name: user,
      fieldname: "new_password",
      value: newPassword.value,
    };
  },
  onSuccess() {
    toast.success("Password updated successfully");
    show.value = false;
    newPassword.value = "";
    confirmPassword.value = "";
    error.value = "";
  },
  onError(err) {
    error.value = err.messages[0] || "Failed to update password";
  },
});

function isStrongPassword(password) {
  const strongPasswordRegex =
    /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
  return strongPasswordRegex.test(password);
}

watch([newPassword, confirmPassword], () => {
  confirmPasswordMessage.value = "";
  newPasswordMessage.value = "";

  if (newPassword.value.length < 8) {
    newPasswordMessage.value = "Password must be at least 8 characters";
  } else if (!isStrongPassword(newPassword.value)) {
    newPasswordMessage.value =
      "Password must contain uppercase, lowercase, number, and symbol";
  }

  if (
    confirmPassword.value.length &&
    newPassword.value !== confirmPassword.value
  ) {
    confirmPasswordMessage.value = "Passwords do not match";
  } else if (
    newPassword.value === confirmPassword.value &&
    newPassword.value.length &&
    confirmPassword.value.length
  ) {
    confirmPasswordMessage.value = "Passwords match";
  }
});
</script>
<style scoped></style>
