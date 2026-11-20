/** Boot flags setup for a System Manager on a v2 site, from HD Settings.setup_complete alone. */
export function isSetupPending(): boolean {
  return !!window.setup_pending;
}
