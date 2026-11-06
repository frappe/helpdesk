/** The feedback dialog is only useful while telemetry is on, since capture is a no-op otherwise. */
export const canAskForFeedback = (telemetry: { isEnabled: boolean }) =>
  telemetry.isEnabled === true;
