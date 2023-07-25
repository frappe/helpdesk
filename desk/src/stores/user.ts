import { defineStore } from "pinia";
import { createResource } from "frappe-ui";
import { keyBy } from "lodash";

type User = {
  email: string;
  full_name: string;
  name: string;
  user_image: string;
  username: string;
};

export const useUserStore = defineStore("user", () => {
  const d__ = createResource({
    url: "helpdesk.api.user.get_all",
    cache: "Users",
    auto: true,
    transform(data) {
      return keyBy(data, (u) => u.name);
    },
  });

  function getUser(user: string) {
    const data = d__.data;
    return (data ? data[user] : {}) as User;
  }

  return {
    getUser,
  };
});
