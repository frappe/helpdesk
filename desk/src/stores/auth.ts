import { computed, ComputedRef } from "vue";
import { defineStore } from "pinia";
import { createResource, call } from "frappe-ui";
import { isEmpty } from "lodash";
import { router, LOGIN } from "@/router";
import { createToast } from "@/utils";

const URI_LOGIN = "login";
const URI_LOGOUT = "logout";
const URI_SIGNUP = "helpdesk.api.account.signup";
const URI_USER_INFO = "helpdesk.api.auth.get_user";
const URI_VERIFY = "helpdesk.api.account.verify_and_create_account";

/**
 * This is supposed to be the entry point of authentication. This will be
 * called from router itself. Hence the router instance from `useRouter()` will
 * not be available. All Authentication related logic should go in this file.
 * Some of these might contain async methods, beware. */
export const useAuthStore = defineStore("auth", () => {
  const userInfo = createResource({
    url: URI_USER_INFO,
  });
  const init = userInfo.fetch;
  const reloadUser = userInfo.reload;

  const user__ = computed(() => userInfo.data || {});
  const hasDeskAccess: ComputedRef<boolean> = computed(
    () => user__.value.has_desk_access
  );
  const isAdmin: ComputedRef<boolean> = computed(() => user__.value.is_admin);
  const isAgent: ComputedRef<boolean> = computed(() => user__.value.is_agent);
  const isLoggedIn: ComputedRef<boolean> = computed(
    () => !isEmpty(user__.value)
  );
  const userId: ComputedRef<string> = computed(() => user__.value.user_id);
  const userImage: ComputedRef<string> = computed(
    () => user__.value.user_image
  );
  const userFirstName: ComputedRef<string> = computed(
    () => user__.value.user_first_name
  );
  const userName: ComputedRef<string> = computed(() => user__.value.user_name);
  const username: ComputedRef<string> = computed(() => user__.value.username);

  const login = createResource({
    url: URI_LOGIN,
    onError() {
      throw new Error("Invalid email or password");
    },
    onSuccess() {
      router.replace({ path: "/" });
    },
  });

  const signup = createResource({
    url: URI_SIGNUP,
  });

  const verify = createResource({
    url: URI_VERIFY,
    onSuccess() {
      login.submit({
        usr: verify.params.email,
        pwd: verify.params.password,
      });
    },
    onError() {
      createToast({
        title: "Error verifying account",
        icon: "x",
        iconClasses: "text-red-500",
      });
    },
  });

  function logout() {
    call(URI_LOGOUT).then(() => router.push({ name: LOGIN }));
  }

  return {
    hasDeskAccess,
    init,
    isAdmin,
    isAgent,
    isLoggedIn,
    login,
    logout,
    reloadUser,
    signup,
    userFirstName,
    userId,
    userImage,
    userName,
    username,
    verify,
  };
});
