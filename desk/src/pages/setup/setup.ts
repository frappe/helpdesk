import { capture } from "@/telemetry";
import { validateEmailWithZod } from "@/utils";
import { call } from "frappe-ui";
import { computed, reactive } from "vue";
import { markSetupDoneLocally } from "./gate";

export type StepKey = "password" | "workspace" | "email" | "team";
type Step = { key: StepKey; required?: boolean };
export type InviteRow = {
  id: number;
  email: string;
  role: string;
  sent: boolean;
};
export type Mailbox = { name: string; address: string };

const ALL_STEPS: Step[] = [
  { key: "password", required: true },
  { key: "workspace" },
  { key: "email" },
  { key: "team" },
];
export const normalizeEmail = (email: string) => email.trim().toLowerCase();

let nextRowId = 1;
export const newRow = (email = "", role = "Agent"): InviteRow => ({
  id: nextRowId++,
  email,
  role,
  sent: false,
});

export const setup = reactive({
  step: (window.setup_complete ? "workspace" : "password") as StepKey,
  askPassword: !window.setup_complete,
  password: "",
  brandName: "",
  brandLogo: "",
  mailbox: null as Mailbox | null,
  ticketArrived: false,
  rows: [newRow()],
  showDone: false,
});

export const steps = computed(() =>
  ALL_STEPS.filter(
    (s) =>
      (s.key !== "password" || setup.askPassword) &&
      (s.key !== "team" || setup.mailbox)
  )
);
export const stepIndex = computed(() =>
  steps.value.findIndex((s) => s.key === setup.step)
);
export const currentStep = computed(() => steps.value[stepIndex.value]);
export const canGoBack = computed(
  () => stepIndex.value > 0 && !steps.value[stepIndex.value - 1].required
);

/** Valid, unique emails typed on the Team step, in order. */
export const invitees = computed(() => {
  const seen = new Set<string>();
  return setup.rows.flatMap((row) => {
    const email = normalizeEmail(row.email);
    if (!validateEmailWithZod(email) || seen.has(email)) return [];
    seen.add(email);
    return [{ email, sent: row.sent }];
  });
});
export const invited = computed(() =>
  invitees.value.filter((i) => i.sent).map((i) => i.email)
);

const site = window.location.host;
/** The company name, or the site's subdomain until one is typed. */
export const brand = computed(() => {
  const name = setup.brandName.trim();
  if (name) return name;
  const host = site.split(".")[0];
  return host.charAt(0).toUpperCase() + host.slice(1);
});

const funnel = {
  stepStartedAt: Date.now(),
  completed: [] as StepKey[],
  skipped: [] as StepKey[],
};

function track(event: string, data: Record<string, string | number> = {}) {
  capture(event, {
    data: {
      step: setup.step,
      step_number: stepIndex.value + 1,
      total_steps: steps.value.length,
      duration_seconds: Math.round((Date.now() - funnel.stepStartedAt) / 1000),
      ...data,
    },
  });
}

const STEP_KEY = "helpdesk-setup-step";

function goTo(step: StepKey) {
  setup.step = step;
  sessionStorage.setItem(STEP_KEY, step);
  funnel.stepStartedAt = Date.now();
}

/** Opens `step`, else the step this tab was on before it left, e.g. for a sign-in page. */
export function startSetup(step?: StepKey) {
  step ??= (sessionStorage.getItem(STEP_KEY) as StepKey | null) ?? undefined;
  if (step && steps.value.some((s) => s.key === step)) goTo(step);
  track("started_setup");
}

/** Moves on from the current step, or opens the done dialog after the last one. */
export function next({ skipped = false } = {}) {
  const from = setup.step;
  track(skipped ? "skipped_setup_step" : "completed_setup_step");
  (skipped ? funnel.skipped : funnel.completed).push(from);
  const following = steps.value[stepIndex.value + 1];
  if (following) return goTo(following.key);
  finishSetup();
}

let stepBack: (() => boolean) | null = null;

/** Lets the current step handle Back itself first, e.g. a provider form returning to the provider list. */
export function setStepBack(handler: (() => boolean) | null) {
  stepBack = handler;
}

export function back() {
  if (stepBack?.()) return;
  if (!canGoBack.value) return;
  const to = steps.value[stepIndex.value - 1].key;
  track("went_back_in_setup", { from_step: setup.step, to_step: to });
  goTo(to);
}

export function skipSetup() {
  track("left_setup");
  finishSetup();
}

function finishSetup() {
  markSetupDoneLocally();
  capture("setup_completed", {
    data: { completed_steps: funnel.completed, skipped_steps: funnel.skipped },
  });
  completing = call("helpdesk.api.setup.complete_setup").catch(() => {});
  setup.showDone = true;
}

let completing: Promise<unknown> = Promise.resolve();

/** Opens the desk once the server has ended setup, with a fresh boot: finishing can make the admin an agent. */
export async function openDesk() {
  await completing;
  window.location.replace("/helpdesk/home");
}
