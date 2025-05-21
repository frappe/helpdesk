import { LOGIN_PAGE } from "@/router";
import { createResource } from "frappe-ui";
import { defineStore } from "pinia";
import { reactive, ref } from "vue";
import { useAuthStore } from "./auth";

export const useUserStore = defineStore("user", () => {
  const auth = useAuthStore();
  const usersByName = reactive({});
  const userRoles = ref<Record<string, string>>({});

  const users = createResource({
    url: "helpdesk.api.session.get_users",
    cache: "Users",
    initialData: [],
    transform(users) {
      for (const user of users) {
        user.full_name = formatFullName(user.email);
        usersByName[user.name] = user;
      }
      return users;
    },
    onError(error) {
      if (error && error.exc_type === "AuthenticationError") {
        window.location.href = LOGIN_PAGE;
      }
    },
  });

  const init = users.fetch;

  function getUser(email) {
    if (!email || email === "sessionUser") {
      email = auth.username;
    }
    if (!usersByName[email]) {
      usersByName[email] = {
        name: email,
        email: email,
        full_name: formatFullName(email),
        user_image: null,
        role: null,
      };
    }
    return usersByName[email];
  }
  function formatFullName(email) {
    let name = email.split("@")[0];
    name = name.charAt(0).toUpperCase() + name.slice(1);
    return name;
  }

  function getUserRole(email: string) {
    if (!email || email === "sessionUser") {
      email = auth.username;
    }
    if (userRoles.value[email]) {
      return userRoles.value[email];
    }
    const user = getUser(email);
    const calculatedRole = user.role;
    userRoles.value[email] = calculatedRole;
    return calculatedRole;
  }

  function updateUserRoleCache(user: string, role: string) {
    userRoles.value[user] = role;
  }

  return {
    users,
    init,
    getUser,
    getUserRole,
    updateUserRoleCache,
  };
});
