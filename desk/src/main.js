import {
  Badge,
  Button,
  Dialog,
  ErrorMessage,
  FeatherIcon,
  FormControl,
  frappeRequest,
  Input,
  resourcesPlugin,
  setConfig,
  TextInput,
  toast,
  Tooltip,
} from "frappe-ui";
import { createPinia } from "pinia";
import { createApp } from "vue";
import App from "./App.vue";
import { createDialog } from "./components/dialogs";
import "./index.css";
import { router } from "./router";
import { socket } from "./socket";
import { posthogPlugin } from "./telemetry";
import { translationsPlugin } from "./plugins/translationsPlugin";

const globalComponents = {
  Badge,
  Button,
  Dialog,
  ErrorMessage,
  FeatherIcon,
  FormControl,
  Input,
  Tooltip,
  TextInput,
};

setConfig("resourceFetcher", frappeRequest);
setConfig("fallbackErrorHandler", (error) => {
  const msg = error.exc_type
    ? (error.messages || error.message || []).join(", ")
    : error.message;
  toast.error(msg);
});

const pinia = createPinia();
const app = createApp(App);

app.use(resourcesPlugin);
app.use(translationsPlugin);
app.use(pinia);
app.use(router);
app.use(posthogPlugin);
for (const c in globalComponents) {
  app.component(c, globalComponents[c]);
}

app.config.globalProperties.$socket = socket;
app.config.globalProperties.$dialog = createDialog;

if (import.meta.env.DEV) {
  frappeRequest({
    url: "/api/method/helpdesk.www.helpdesk.index.get_context_for_dev",
  }).then((values) => {
    if (!window.frappe) window.frappe = {};
    window.frappe.boot = values;
    app.mount("#app");
  });
} else {
  app.mount("#app");
}
