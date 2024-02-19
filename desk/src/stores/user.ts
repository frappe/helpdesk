import { defineStore } from "pinia";
import { createResource } from "frappe-ui";
import { useAuthStore } from "./auth";
import { reactive } from "vue";
import { router } from "@/router";

export const useUserStore = defineStore("user", () => {
  const auth = useAuthStore();
  const usersByName = reactive({});

  const users = createResource({
    url: "helpdesk.api.session.get_users",
    cache: "Users",
    initialData: [],
    transform(users) {
      for (const user of users) {
        usersByName[user.name] = user;
      }
      return users;
    },
    onError(error) {
      if (error && error.exc_type === "AuthenticationError") {
        router.push("/login");
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
        full_name: email.split("@")[0],
        user_image: null,
        role: null,
      };
    }
    return usersByName[email];
  }

  return {
    users,
    getUser,
    init,
  };
});
