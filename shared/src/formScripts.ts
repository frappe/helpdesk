import { toast } from "frappe-ui";
import { h, isVNode, type Component } from "vue";
import { __ } from "./translation";

// HD Form Script runtime, shared by the desk and the Studio portal.

type ToastType = "success" | "error" | "warning" | "info";

let spriteLoad: Promise<unknown> | undefined;

// Any lucide icon, from frappe-ui's sprite; the portal fetches it on first use.
export function ScriptIcon({ icon }: { icon: string }) {
  if (!document.getElementById("lucide-sprite")) {
    spriteLoad ??= import("frappe-ui/experimental").then(({ spritePlugin }) =>
      spritePlugin.install()
    );
  }
  return h(
    "svg",
    {
      class: "size-4",
      viewBox: "0 0 24 24",
      fill: "none",
      stroke: "currentColor",
      "stroke-width": 1.5,
      "stroke-linecap": "round",
      "stroke-linejoin": "round",
      "aria-hidden": "true",
    },
    [h("use", { href: `#${icon.replace("lucide-", "")}` })]
  );
}

// vue-sonner renders icons via `<component :is>`, so each legacy shape becomes a component.
function resolveIcon(icon: unknown): Component | undefined {
  if (icon == null) return undefined;
  if (typeof icon === "string") {
    // Anything but an icon name, such as an emoji, shows as text.
    if (!/^[\w-]+$/.test(icon)) return () => h("span", icon);
    return () => h(ScriptIcon, { icon });
  }
  if (isVNode(icon)) return () => icon;
  return icon as Component;
}

// Keeps frappe-ui's pre-v1 `toast.create({ message, ... })` alive for form scripts.
export function createToast({
  message,
  type,
  icon,
  ...options
}: {
  message: string;
  type?: ToastType;
  icon?: unknown;
  [key: string]: unknown;
}) {
  const data: Record<string, unknown> = { ...options };
  if (icon) data.icon = resolveIcon(icon);
  if (typeof options.duration === "number") {
    data.duration = toMilliseconds(options.duration);
  }
  return type ? toast[type](message, data) : toast(message, data);
}

// The old API took seconds, with 0 meaning stay open.
function toMilliseconds(seconds: number) {
  return seconds === 0 ? Infinity : seconds * 1000;
}

export async function setupCustomizations(doc, obj) {
  // Supporting old format, will have to refactor later
  let data = doc.data ?? doc;
  if (!data) return;
  if (!data._form_script) return [];
  const scripts = Array.isArray(data._form_script)
    ? data._form_script
    : [data._form_script];
  let actions = [];
  let links = [];
  let onChangeFieldMap = {};
  for (const script of scripts) {
    const parsed = await parseScript(script, obj);
    actions = actions.concat(parsed.actions);
    links = links.concat(parsed.links);
    if (parsed.onChange) {
      parseOnChangeFn(onChangeFieldMap, parsed.onChange);
    }
  }
  data._customActions = withLegacyGroupOptions(actions);
  data._customLinks = links;
  if (Object.keys(onChangeFieldMap).length) {
    data._customOnChange = onChangeFieldMap;
  }
}

// Pre-v1 form scripts name a group's children `items`, which the menu no longer reads.
function withLegacyGroupOptions(actions: any[]) {
  return actions.map((action) =>
    action.items && !action.options
      ? { ...action, options: action.items }
      : action
  );
}

function parseOnChangeFn(fieldMap: object, currentField: object) {
  for (const [key, value] of Object.entries(currentField)) {
    if (!fieldMap[key]) {
      fieldMap[key] = new Set();
    }
    fieldMap[key].add(value);
  }
}

// A broken script is skipped, so the page and the other scripts still work.
async function parseScript(script, obj) {
  try {
    const scriptFn = new Function(script + "\nreturn setupForm")();
    const formScript = await scriptFn(obj);
    return {
      actions: formScript?.actions || [],
      links: formScript?.links || [],
      onChange: formScript?.onChange || null,
    };
  } catch (error) {
    console.error(error);
    toast.error(__("A form script on this page failed to run"));
    return { actions: [], links: [], onChange: null };
  }
}

export function handleSelectFieldUpdate(
  f: any,
  fieldname: string,
  filters: any,
  doc: any,
  oldDoc: any
) {
  if (!filters || !filters.length) {
    f.options = oldDoc.find((f) => f.fieldname === fieldname).options;
    f.disabled = true;
  } else {
    f.options = filters.join("\n");
    f.disabled = false;
  }
  // reset dependent field
  doc[fieldname] = "";
}

export function handleLinkFieldUpdate(
  f: any,
  fieldname: string,
  filters: any,
  doc: any,
  oldDoc: any
) {
  if (!filters || !filters.length) {
    f.link_filters = oldDoc.find((f) => f.fieldname === fieldname).link_filters;
    f.disabled = true;
    return;
  }
  f.link_filters = JSON.stringify([[f.options, "name", "in", filters]]);
  f.disabled = false;

  // reset dependent field
  doc[fieldname] = "";
}
