import LucideChevronUp from "~icons/lucide/chevron-up";
import LucideCommand from "~icons/lucide/command";

/**
 * Helper values to determine the device type/make etc.
 * @returns An object containing device information
 */
export function useDevice() {
  const isMac = navigator.userAgent.indexOf("Mac OS X") != -1;
  const controlKey = isMac ? "⌃" : "Ctrl";
  const altKey = isMac ? "⌥" : "Alt";
  const metaKey = isMac ? "⌘" : "Meta";
  const modifier = isMac ? "meta" : "control";
  const modifierIcon = isMac ? LucideCommand : LucideChevronUp;
  return {
    altKey,
    controlKey,
    isMac,
    metaKey,
    modifier,
    modifierIcon,
  };
}
