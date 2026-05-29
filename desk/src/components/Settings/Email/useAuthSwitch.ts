import { __ } from "@/translation";
import { createResource, toast } from "frappe-ui";
import { computed, reactive, ref, watch, type ComputedRef, type Ref } from "vue";
import type { AuthMethod } from "../emailConfig";

interface SwitchPayload {
  email_account: string;
  auth_method: AuthMethod;
  service: string;
  client_id?: string;
  client_secret?: string;
  password?: string;
}

interface UseAuthSwitchArgs {
  emailAccountName: Ref<string>;
  service: ComputedRef<string>;
  currentAuthMethod: ComputedRef<AuthMethod>;
  onSwitched: () => void;
}

export function useAuthSwitch({
  emailAccountName,
  service,
  currentAuthMethod,
  onSwitched,
}: UseAuthSwitchArgs) {
  const authMethod = ref<AuthMethod>(currentAuthMethod.value);
  const authMethodOptions = [
    { label: __("OAuth"), value: "OAuth" },
    { label: __("Basic (App Password)"), value: "Basic" },
  ];
  const switchState = reactive({
    client_id: "",
    client_secret: "",
    password: "",
  });
  const error = ref<string | undefined>();

  const isAuthMethodChanged = computed(
    () => authMethod.value !== currentAuthMethod.value
  );

  watch(currentAuthMethod, (value) => {
    authMethod.value = value;
  });

  const switchAuthRes = createResource({
    url: "helpdesk.api.settings.email.switch_email_auth_method",
    onSuccess: (data: { redirect_url?: string; auth_method?: AuthMethod }) => {
      if (data?.redirect_url) {
        window.location.href = data.redirect_url;
        return;
      }
      toast.success(
        data?.auth_method === "Basic"
          ? __("Switched to Basic auth")
          : __("Switched authentication method")
      );
      onSwitched();
    },
    onError: (err: { messages?: string[]; message?: string }) => {
      error.value =
        err?.messages?.[0] ||
        err?.message ||
        __("Failed to switch authentication method");
    },
  });

  function validate(): string {
    if (authMethod.value === "OAuth") {
      if (!switchState.client_id || !switchState.client_secret)
        return __("Client ID and Client Secret are required");
      return "";
    }
    if (!switchState.password) return __("App password is required");
    return "";
  }

  function submit() {
    error.value = validate() || undefined;
    if (error.value) return;
    const payload: SwitchPayload = {
      email_account: emailAccountName.value,
      auth_method: authMethod.value,
      service: service.value,
      client_id: switchState.client_id,
      client_secret: switchState.client_secret,
      password: switchState.password,
    };
    switchAuthRes.submit({ data: payload });
  }

  return {
    authMethod,
    authMethodOptions,
    switchState,
    isAuthMethodChanged,
    switchAuthRes,
    submit,
    error,
  };
}
