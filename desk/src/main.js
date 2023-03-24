import { createApp } from "vue";
import { createPinia } from "pinia";
import {
	FrappeUI,
	Badge,
	Button,
	Dialog,
	Input,
	Tooltip,
	frappeRequest,
	setConfig,
	onOutsideClickDirective,
} from "frappe-ui";
import * as lodash from "lodash";
import router from "./router";
import App from "./App.vue";
import "./index.css";
import { clipboardCopy } from "@/utils/clipboard";
import { createToast, clearToasts } from "@/utils/toasts";
import { dayjs } from "@/utils";
import { event } from "@/utils/event";
import { socketio_port } from "../../../../sites/common_site_config.json";

const pinia = createPinia();
const app = createApp(App);

setConfig("resourceFetcher", frappeRequest);

app.directive("on-outside-click", onOutsideClickDirective);
app.use(pinia);
app.use(router);
app.use(FrappeUI, {
	socketio: {
		port: socketio_port,
	},
});

app.component("Button", Button);
app.component("Dialog", Dialog);
app.component("Input", Input);
app.component("Tooltip", Tooltip);
app.component("Badge", Badge);

app.config.unwrapInjectedRef = true;

app.config.globalProperties.$_ = lodash;
app.config.globalProperties.$clearToasts = clearToasts;
app.config.globalProperties.$clipboardCopy = clipboardCopy;
app.config.globalProperties.$dayjs = dayjs;
app.config.globalProperties.$event = event;
app.config.globalProperties.$toast = createToast;

app.mount("#app");
