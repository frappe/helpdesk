import * as lodash from "lodash";
import { createApp } from "vue";
import { createPinia } from "pinia";
import {
  frappeRequest,
  resourcesPlugin,
  setConfig,
  Badge,
  Button,
  Dialog,
  ErrorMessage,
  FeatherIcon,
  FormControl,
  Input,
  Tooltip,
} from "frappe-ui";
import App from "./App.vue";
import "./index.css";
import { router } from "./router";
import { socket } from "./socket";
import { createToast } from "@/utils";

const globalComponents = {
  Badge,
  Button,
  Dialog,
  ErrorMessage,
  FeatherIcon,
  FormControl,
  Input,
  Tooltip,
};

setConfig("resourceFetcher", frappeRequest);
setConfig("fallbackErrorHandler", (error) => {
  createToast({
    title: error.exc_type || "Error",
    text: (error.messages || []).join(", "),
    icon: "alert-triangle",
    iconClasses: "text-red-500",
  });
});

const pinia = createPinia();
const app = createApp(App);

app.use(resourcesPlugin);
app.use(pinia);
app.use(router);

for (const c in globalComponents) {
  app.component(c, globalComponents[c]);
}

app.config.unwrapInjectedRef = true;
app.config.globalProperties.$_ = lodash;
app.config.globalProperties.$socket = socket;
app.config.globalProperties.$toast = createToast;

app.mount("#app");
