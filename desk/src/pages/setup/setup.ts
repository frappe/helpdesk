import { capture } from "@/telemetry";
import { __ } from "@/translation";
import { validateEmailWithZod } from "@/utils";
import { useTelemetry } from "@framework/ui";
import { until, useIntervalFn } from "@vueuse/core";
import { call, toast } from "frappe-ui";
import {
  computed,
  inject,
  type InjectionKey,
  provide,
  reactive,
  ref,
  watch,
} from "vue";

export type StepKey = "password" | "workspace" | "email" | "team";
type Step = { key: StepKey; required?: boolean };
export type InviteRow = {
  id: number;
  email: string;
  role: string;
  sent: boolean;
};
export type Mailbox = { name: string; address: string };
type SetupOutcome = {
  skipped_setup: boolean;
  completed_steps: StepKey[];
  skipped_steps: StepKey[];
};

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

  const startedAt = Date.now();
  let stepStartedAt = startedAt;
  const secondsSince = (start: number) =>
    Math.round((Date.now() - start) / 1000);
  const stepStatus: Partial<Record<StepKey, "completed" | "skipped">> = {};
  const stepsWith = (status: "completed" | "skipped") =>
    (Object.keys(stepStatus) as StepKey[]).filter(
      (step) => stepStatus[step] === status
    );
  const outcome = ref<SetupOutcome | null>(null);

  function viewed() {
    stepStartedAt = Date.now();
    capture("setup_step_viewed", { data: { step: setup.step } });
  }

  let movedAt = 0;

  function holdEnter(event: KeyboardEvent) {
    if (event.key !== "Enter" || event.target instanceof HTMLTextAreaElement)
      return;
    if (!event.repeat && performance.now() - movedAt >= SETTLE_MS) return;
    event.preventDefault();
    event.stopPropagation();
  }

  function open(step: StepKey) {
    movedAt = performance.now();
    setup.step = step;
    sessionStorage.setItem(STEP_KEY, step);
  }

  function goTo(step: StepKey) {
    open(step);
    viewed();
  }

  const telemetry = useTelemetry();

  function startSetup(step?: StepKey) {
    step ??= (sessionStorage.getItem(STEP_KEY) as StepKey | null) ?? undefined;
    if (step && steps.value.some((s) => s.key === step)) open(step);
    const first = setup.step;
    until(() => telemetry.isEnabled)
      .toBe(true)
      .then(() => {
        capture("setup_started");
        capture("setup_step_viewed", { data: { step: first } });
      });
  }

  function next({ skipped = false } = {}) {
    const step = setup.step;
    if (!skipped || stepStatus[step] !== "completed")
      stepStatus[step] = skipped ? "skipped" : "completed";
    capture(skipped ? "setup_step_skipped" : "setup_step_completed", {
      data: {
        step,
        time_on_step_s: secondsSince(stepStartedAt),
      },
    });
    const following = steps.value[stepIndex.value + 1];
    if (following) return goTo(following.key);
    finishSetup(false);
  }

  let stepBack: (() => boolean) | null = null;

  function setStepBack(handler: (() => boolean) | null) {
    stepBack = handler;
  }

  function back() {
    if (stepBack?.()) return;
    if (!canGoBack.value) return;
    capture("setup_back", { data: { from_step: setup.step } });
    goTo(steps.value[stepIndex.value - 1].key);
  }

  function skipSetup() {
    capture("setup_skipped", { data: { step: setup.step } });
    finishSetup(true);
  }

  function reportError(action: string, error: unknown) {
    const e = error as { exc_type?: string; name?: string; status?: number };
    capture("setup_error", {
      data: {
        step: setup.step,
        action,
        error_type:
          typeof error === "string" ? error : e?.exc_type || e?.name || "Error",
        status: e?.status ?? null,
      },
    });
  }

  let completing: Promise<string | null> = Promise.resolve(null);

  function completeSetup() {
    return call<string | null>("helpdesk.api.setup.complete_setup");
  }

  function finishSetup(skipped: boolean) {
    outcome.value = {
      skipped_setup: skipped,
      completed_steps: stepsWith("completed"),
      skipped_steps: stepsWith("skipped"),
    };
    capture("setup_finished", {
      data: {
        skipped,
        duration_s: secondsSince(startedAt),
        steps_completed: outcome.value.completed_steps.length,
      },
    });
    completing = completeSetup();
    completing.catch((e) => reportError("complete_setup", e));
    movedAt = performance.now();
    setup.showDone = true;
  }

  /** Leaves only once HD Settings records the setup, retrying a failed save, so the desk does not send the user back. */
  async function openDesk() {
    try {
      const ticket = await completing.catch(completeSetup);
      window.location.replace(`/helpdesk/tickets/${ticket ?? ""}`);
    } catch (e) {
      reportError("complete_setup", e);
      toast.error(__("Could not finish setup. Please try again."));
    }
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
    /** Opens `step`, else the step this tab was on before it left, e.g. for a sign-in page.
     * Its first events wait for telemetry, which loads after the page starts. */
    startSetup,
    /** Moves on from the current step, or opens the done dialog after the last one. */
    next,
    /** Lets the current step handle Back itself first, e.g. a provider form returning to the list. */
    setStepBack,
    back,
    skipSetup,
    /** Sends `setup_error` for a failed `action`: the error's type and HTTP status, never its message. */
    reportError,
    /** How setup ended, sent along with the done dialog's feedback. */
    outcome,
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
