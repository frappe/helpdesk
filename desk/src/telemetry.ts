import { useStorage } from "@vueuse/core";
import { call } from "frappe-ui";
import "../../../frappe/frappe/public/js/lib/posthog.js";

const APP = "helpdesk";
const SITENAME = window.location.hostname;

// extend window object to add posthog
// eslint-disable-next-line @typescript-eslint/no-explicit-any
declare global {
  interface Window {
    posthog: any;
  }
}

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
    window.posthog.init(telemetry.value.project_id, {
      api_host: telemetry.value.host,
      autocapture: false,
      person_profiles: "always",
      capture_pageview: true,
      capture_pageleave: true,
      disable_session_recording: false,
      session_recording: {
        maskAllInputs: false,
        maskInputOptions: {
          password: true,
        },
      },
      loaded: (posthog) => {
        window.posthog = posthog;
        window.posthog.identify(SITENAME);
      },
    });
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

interface CaptureOptions {
  data: {
    user: string;
    [key: string]: string | number | boolean | object;
  };
}

export function capture(
  event: string,
  options: CaptureOptions = { data: { user: "" } }
) {
  if (!telemetry.value.enabled) return;
  window.posthog.capture(`${APP}_${event}`, options);
}

export function recordSession() {
  if (!telemetry.value.enabled) return;
  if (window.posthog && window.posthog.__loaded) {
    window.posthog.startSessionRecording();
  }
}

export function stopSession() {
  if (!telemetry.value.enabled) return;
  if (
    window.posthog &&
    window.posthog.__loaded &&
    window.posthog.sessionRecordingStarted()
  ) {
    window.posthog.stopSessionRecording();
  }
}
