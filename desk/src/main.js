import * as lodash from "lodash";
import { createApp } from "vue";
import { createPinia } from "pinia";
import {
	Badge,
	Button,
	Dialog,
	Input,
	Tooltip,
	frappeRequest,
	onOutsideClickDirective,
	resourcesPlugin,
	setConfig,
} from "frappe-ui";
import App from "./App.vue";
import "./index.css";
import { router } from "./router";
import { socket } from "./socket";
import { clipboardCopy } from "@/utils/clipboard";
import { createToast, clearToasts } from "@/utils/toasts";
import { dayjs } from "@/utils";
import { event } from "@/utils/event";

const globalComponents = {
	Badge,
	Button,
	Dialog,
	Input,
	Tooltip,
};

setConfig("resourceFetcher", frappeRequest);

const pinia = createPinia();
const app = createApp(App);

app.directive("on-outside-click", onOutsideClickDirective);
app.use(resourcesPlugin);
app.use(pinia);
app.use(router);

for (const c in globalComponents) {
	app.component(c, globalComponents[c]);
}

app.config.unwrapInjectedRef = true;

app.config.globalProperties.$_ = lodash;
app.config.globalProperties.$clearToasts = clearToasts;
app.config.globalProperties.$clipboardCopy = clipboardCopy;
app.config.globalProperties.$dayjs = dayjs;
app.config.globalProperties.$event = event;
app.config.globalProperties.$socket = socket;
app.config.globalProperties.$toast = createToast;

app.mount("#app");
