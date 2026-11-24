import { capture } from "@/telemetry";
import { __ } from "@/translation";
import type { StepBack } from "@framework/ui";
import { useIntervalFn } from "@vueuse/core";
import { call, toast } from "frappe-ui";
import { useRouter } from "vue-router";
import { preloadLayout } from "@/components/layouts/layouts";
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
type Step = { name: StepKey; required?: boolean };
export type Mailbox = { name: string; address: string };
/** A row of the preview's ticket list. */
export type TicketRow = {
  id: string;
  subject: string;
  status: string;
  response: string;
  assigned: string;
  priority: string;
  created: string;
};

const ALL_STEPS: Step[] = [
  { name: "password", required: true },
  { name: "workspace" },
  { name: "email" },
  { name: "team" },
];
const STEP_KEY = "helpdesk-setup-step";
const SETTLE_MS = 500;
const IMPORT_PHASE_SECONDS = 5;
export const IMPORT_PHASES = 3;

export const normalizeEmail = (email: string) => email.trim().toLowerCase();

function createSetupFlow() {
  const router = useRouter();
  const setup = reactive({
    step: undefined as StepKey | undefined,
    askPassword: window.needs_password_setup,
    passwordLength: 0,
    passwordReady: false,
    brandName: "",
    brandLogo: "",
    mailbox: null as Mailbox | null,
    ticketArrived: false,
    /** Valid emails typed on the Team step, as the step reports them. */
    typed: [] as { email: string; role: string }[],
    /** Emails the Team step has invited. */
    sentTo: [] as string[],
    /** True once setup ends: the preview grows into the ticket list the desk opens. */
    handingOver: false,
    /** The site's own tickets, swapped into the preview just before it grows. */
    landing: null as TicketRow[] | null,
    /** The welcome ticket the server returns when setup ends, which the desk opens first. */
    welcomeTicket: null as string | null,
    /** The real ticket page the preview opens at the hand-over, loaded behind the list. */
    landingTicket: null as string | null,
    landingOpen: false,
  });

  const steps = computed(() =>
    ALL_STEPS.filter(
      (s) =>
        (s.name !== "password" || setup.askPassword) &&
        (s.name !== "team" || setup.mailbox)
    )
  );

  const invitees = computed(() => {
    const seen = new Set<string>();
    return setup.typed.flatMap((row) => {
      const email = normalizeEmail(row.email);
      if (seen.has(email)) return [];
      seen.add(email);
      return [{ email, sent: setup.sentTo.includes(email) }];
    });
  });
  const invited = computed(() => [...new Set(setup.sentTo)]);

  const brand = computed(() => {
    const name = setup.brandName.trim();
    return name || __("Frappe Helpdesk");
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

  let movedAt = 0;
  let shellReady: Promise<unknown> = Promise.resolve();

  function holdEnter(event: KeyboardEvent) {
    if (event.key !== "Enter" || event.target instanceof HTMLTextAreaElement)
      return;
    if (!event.repeat && performance.now() - movedAt >= SETTLE_MS) return;
    event.preventDefault();
    event.stopPropagation();
  }

  // The step on screen comes back after a sign-in page, which leaves setup mid-way.
  const saved = (
    new URLSearchParams(window.location.search).has("email_oauth")
      ? "email"
      : sessionStorage.getItem(STEP_KEY)
  ) as StepKey | null;
  if (saved && steps.value.some((s) => s.name === saved)) setup.step = saved;
  watch(
    () => setup.step,
    (step) => {
      movedAt = performance.now();
      if (step) sessionStorage.setItem(STEP_KEY, step);
    }
  );

  // SetupFlow hands each step its own actions; the steps reach them through here.
  const actions = {
    done: () => {},
    skip: () => {},
    handleBack: (_: StepBack | null) => {},
  };
  function bindStep(step: typeof actions) {
    Object.assign(actions, step);
    return {};
  }

  function next({ skipped = false } = {}) {
    if (skipped) actions.skip();
    else actions.done();
  }

  function setStepBack(handler: StepBack | null) {
    actions.handleBack(handler);
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

  function finishSetup() {
    completing = completeSetup();
    completing
      .then((ticket) => (setup.welcomeTicket = ticket))
      .catch((e) => reportError("complete_setup", e));
    movedAt = performance.now();
    // Below lg the preview is hidden, so there is nothing to grow into the desk.
    if (!window.matchMedia?.("(min-width: 1024px)").matches) return openDesk();
    // The desk shell and its pages load while the preview grows, so the switch shows no blank frame.
    shellReady = Promise.all([
      preloadLayout(false),
      import("@/roots/AgentRoot.vue"),
      import("@/pages/ticket/TicketAgent.vue"),
    ]).catch(() => {});
    setup.handingOver = true;
  }

  /** Leaves only once HD Settings records the setup, retrying a failed save, so the desk does not send the user back. */
  async function openDesk() {
    try {
      const ticket = await completing.catch(completeSetup);
      await shellReady;
      // The router sends a pending setup back here, so it reads the boot flag first.
      window.setup_pending = false;
      await router.replace(
        ticket
          ? { name: "TicketAgent", params: { ticketId: ticket } }
          : { name: "TicketsAgent" }
      );
    } catch (e) {
      reportError("complete_setup", e);
      toast.error(__("Could not finish setup. Please try again."));
    }
  }

  return {
    setup,
    steps,
    /** Valid, unique emails typed on the Team step, in order. */
    invitees,
    invited,
    /** The company name, or the site's subdomain until one is typed. */
    brand,
    /** Seconds-based phase of the mailbox's first import, for the Email step's progress. */
    importPhase,
    /** Drops an Enter that lands while a step is still coming in. */
    holdEnter,
    /** Takes SetupFlow's actions for the step on screen; binds no props. */
    bindStep,
    /** Moves on from the current step; SetupFlow opens the next one or finishes. */
    next,
    /** Lets the current step handle Back itself first, e.g. a provider form returning to the list. */
    setStepBack,
    /** Ends setup, from SetupFlow's finish: saves it and hands over to the desk. */
    finishSetup,
    /** Sends `setup_error` for a failed `action`: the error's type and HTTP status, never its message. */
    reportError,
    /** Opens the welcome ticket once the server has ended setup. */
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
