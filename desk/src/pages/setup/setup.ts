import { capture } from "@/telemetry";
import { validateEmailWithZod } from "@/utils";
import { useIntervalFn } from "@vueuse/core";
import { call } from "frappe-ui";
import {
  computed,
  inject,
  type InjectionKey,
  provide,
  reactive,
  ref,
  watch,
} from "vue";
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
const STEP_KEY = "helpdesk-setup-step";
const SETTLE_MS = 500;
const IMPORT_PHASE_SECONDS = 5;
export const IMPORT_PHASES = 3;

export const normalizeEmail = (email: string) => email.trim().toLowerCase();

function createSetupFlow() {
  let nextRowId = 1;
  const newRow = (email = "", role = "Agent"): InviteRow => ({
    id: nextRowId++,
    email,
    role,
    sent: false,
  });

  const setup = reactive({
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

  const steps = computed(() =>
    ALL_STEPS.filter(
      (s) =>
        (s.key !== "password" || setup.askPassword) &&
        (s.key !== "team" || setup.mailbox)
    )
  );
  const stepIndex = computed(() =>
    steps.value.findIndex((s) => s.key === setup.step)
  );
  const currentStep = computed(() => steps.value[stepIndex.value]);
  const canGoBack = computed(
    () => stepIndex.value > 0 && !steps.value[stepIndex.value - 1].required
  );

  const invitees = computed(() => {
    const seen = new Set<string>();
    return setup.rows.flatMap((row) => {
      const email = normalizeEmail(row.email);
      if (!validateEmailWithZod(email) || seen.has(email)) return [];
      seen.add(email);
      return [{ email, sent: row.sent }];
    });
  });
  const invited = computed(() =>
    invitees.value.filter((i) => i.sent).map((i) => i.email)
  );

  const brand = computed(() => {
    const name = setup.brandName.trim();
    if (name) return name;
    const host = window.location.host.split(".")[0];
    return host.charAt(0).toUpperCase() + host.slice(1);
  });

  const waited = ref(0);
  const importClock = useIntervalFn(() => waited.value++, 1000, {
    immediate: false,
  });
  const importPhase = computed(() =>
    Math.floor(waited.value / IMPORT_PHASE_SECONDS)
  );
  watch(
    () => setup.mailbox?.name,
    (mailbox) => {
      if (!mailbox) return;
      waited.value = 0;
      importClock.resume();
    }
  );
  watch(importPhase, (phase) => {
    if (phase < IMPORT_PHASES) return;
    importClock.pause();
    setup.ticketArrived = true;
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
        duration_seconds: Math.round(
          (Date.now() - funnel.stepStartedAt) / 1000
        ),
        ...data,
      },
    });
  }

  let movedAt = 0;

  function holdEnter(event: KeyboardEvent) {
    if (event.key !== "Enter" || event.target instanceof HTMLTextAreaElement)
      return;
    if (!event.repeat && performance.now() - movedAt >= SETTLE_MS) return;
    event.preventDefault();
    event.stopPropagation();
  }

  function goTo(step: StepKey) {
    movedAt = performance.now();
    setup.step = step;
    sessionStorage.setItem(STEP_KEY, step);
    funnel.stepStartedAt = Date.now();
  }

  function startSetup(step?: StepKey) {
    step ??= (sessionStorage.getItem(STEP_KEY) as StepKey | null) ?? undefined;
    if (step && steps.value.some((s) => s.key === step)) goTo(step);
    track("started_setup");
  }

  function next({ skipped = false } = {}) {
    const from = setup.step;
    track(skipped ? "skipped_setup_step" : "completed_setup_step");
    (skipped ? funnel.skipped : funnel.completed).push(from);
    const following = steps.value[stepIndex.value + 1];
    if (following) return goTo(following.key);
    finishSetup();
  }

  let stepBack: (() => boolean) | null = null;

  function setStepBack(handler: (() => boolean) | null) {
    stepBack = handler;
  }

  function back() {
    if (stepBack?.()) return;
    if (!canGoBack.value) return;
    const to = steps.value[stepIndex.value - 1].key;
    track("went_back_in_setup", { from_step: setup.step, to_step: to });
    goTo(to);
  }

  function skipSetup() {
    track("left_setup");
    finishSetup();
  }

  let completing: Promise<string | null> = Promise.resolve(null);

  function finishSetup() {
    markSetupDoneLocally();
    capture("setup_completed", {
      data: {
        completed_steps: funnel.completed,
        skipped_steps: funnel.skipped,
      },
    });
    completing = call("helpdesk.api.setup.complete_setup").catch(() => null);
    movedAt = performance.now();
    setup.showDone = true;
  }

  async function openDesk() {
    const ticket = await completing;
    window.location.replace(`/helpdesk/tickets/${ticket ?? ""}`);
  }

  return {
    setup,
    newRow,
    steps,
    stepIndex,
    currentStep,
    canGoBack,
    /** Valid, unique emails typed on the Team step, in order. */
    invitees,
    invited,
    /** The company name, or the site's subdomain until one is typed. */
    brand,
    /** Seconds-based phase of the mailbox's first import, for the Email step's progress. */
    importPhase,
    /** Drops an Enter that lands while a step or the done dialog is still coming in. */
    holdEnter,
    /** Opens `step`, else the step this tab was on before it left, e.g. for a sign-in page. */
    startSetup,
    /** Moves on from the current step, or opens the done dialog after the last one. */
    next,
    /** Lets the current step handle Back itself first, e.g. a provider form returning to the list. */
    setStepBack,
    back,
    skipSetup,
    /** Opens the welcome ticket once the server has ended setup, with a fresh boot. */
    openDesk,
  };
}

type SetupFlow = ReturnType<typeof createSetupFlow>;
const SETUP_FLOW: InjectionKey<SetupFlow> = Symbol("setup-flow");

/** Creates the flow in Setup.vue, for its steps and preview to share; it ends with that page. */
export function provideSetupFlow() {
  const flow = createSetupFlow();
  provide(SETUP_FLOW, flow);
  return flow;
}

export function useSetupFlow() {
  return inject(SETUP_FLOW)!;
}
