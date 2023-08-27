import { getPage } from "./utils";

export const AuthPages = {
  path: "",
  meta: {
    auth: false,
  },
  children: [
    {
      path: "/login",
      name: "AuthLogin",
      component: () => getPage("AuthLogin"),
    },
    {
      path: "/signup",
      name: "AuthSignup",
      component: () => getPage("AuthSignup"),
    },
    {
      path: "/verify/:requestKey",
      name: "AuthVerify",
      component: () => getPage("AuthVerify"),
      props: true,
    },
  ],
};
