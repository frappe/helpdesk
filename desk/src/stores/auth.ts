import { LOGIN_PAGE, router } from "@/router";
import { call, createResource } from "frappe-ui";
import { defineStore } from "pinia";
import { computed, ComputedRef, Ref, ref } from "vue";

const URI_LOGIN = "login";
const URI_LOGOUT = "logout";
const URI_USER_INFO = "helpdesk.api.auth.get_user";

/**
 * This is supposed to be the entry point of authentication. This will be
 * called from router itself. Hence the router instance from `useRouter()` will
 * not be available. All Authentication related logic should go in this file.
 * Some of these might contain async methods, beware. */
export const useAuthStore = defineStore("auth", () => {
  const userInfo = createResource({
    url: URI_USER_INFO,
  });
  const init = async () => {
    if (userInfo.fetched) return;
    await userInfo.fetch();
  };
  const reloadUser = userInfo.reload;

  const user__ = computed(() => userInfo.data || {});
  const hasDeskAccess: ComputedRef<boolean> = computed(
    () => user__.value.has_desk_access
  );
  const isAdmin: ComputedRef<boolean> = computed(() => user__.value.is_admin);
  const isAgent: ComputedRef<boolean> = computed(() => user__.value.is_agent);
  const isManager: ComputedRef<boolean> = computed(
    () => user__.value.is_manager
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
  const timezone: ComputedRef<string> = computed(() => user__.value.time_zone);

  function sessionUser() {
    const cookies = new URLSearchParams(document.cookie.split("; ").join("&"));
    let _sessionUser = cookies.get("user_id");
    if (_sessionUser === "Guest") {
      _sessionUser = null;
    }
    return _sessionUser;
  }
  const user: Ref<string> = ref(sessionUser());
  const isLoggedIn: ComputedRef<boolean> = computed(() => !!user.value);
  const login = createResource({
    url: URI_LOGIN,
    onError() {
      throw new Error("Invalid email or password");
    },
    onSuccess() {
      user.value = sessionUser();
      login.reset();
      router.replace({ path: "/" });
    },
  });

  function logout() {
    user.value = null;
    call(URI_LOGOUT).then(() => {
      window.location.href = LOGIN_PAGE;
    });
  }

  return {
    hasDeskAccess,
    init,
    isAdmin,
    isAgent,
    isManager,
    isLoggedIn,
    login,
    reloadUser,
    userFirstName,
    userId,
    userImage,
    userName,
    username,
    timezone,
    user,
    logout,
  };
});
