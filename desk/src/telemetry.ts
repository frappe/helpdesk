import { useStorage } from "@vueuse/core";
import { call } from "frappe-ui";
import "../../../frappe/frappe/public/js/lib/posthog.js";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
declare const posthog: any;

const APP = "helpdesk";
const SITENAME = window.location.hostname;

const telemetry = useStorage("telemetry", {
	enabled: false,
	project_id: "",
	host: "",
});

export async function init() {
	await set_enabled();
	if (!telemetry.value.enabled) return;
	try {
		await set_credentials();
		posthog.init(telemetry.value.project_id, {
			api_host: telemetry.value.host,
			autocapture: false,
			capture_pageview: false,
			capture_pageleave: false,
			advanced_disable_decide: true,
		});
		posthog.identify(SITENAME);
	} catch (e) {
		console.trace("Failed to initialize telemetry", e);
		telemetry.value.enabled = false;
	}
}

async function set_enabled() {
	if (telemetry.value.enabled) return;

	await call("helpdesk.api.telemetry.is_enabled").then((res) => {
		telemetry.value.enabled = res;
	});
}

async function set_credentials() {
	if (!telemetry.value.enabled) return;
	if (telemetry.value.project_id && telemetry.value.host) return;

	await call("helpdesk.api.telemetry.get_credentials").then((res) => {
		telemetry.value.project_id = res.project_id;
		telemetry.value.host = res.telemetry_host;
	});
}

export function capture(event: string) {
	if (!telemetry.value.enabled) return;
	posthog.capture(`${APP}_${event}`);
}
