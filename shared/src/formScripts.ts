import { toast } from "frappe-ui";
import { h, isVNode, type Component } from "vue";
import { __ } from "./translation";

// HD Form Script runtime, shared by the desk and the Studio portal.

type ToastType = "success" | "error" | "warning" | "info";

let spriteLoad: Promise<unknown> | undefined;

// Scripts name any lucide icon, so it comes from frappe-ui's sprite: the desk
// installs it at boot, the portal fetches it the first time a script asks.
// ponytail: the sprite is ~470 KB; an icon list per script is the upgrade if that hurts.
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

// vue-sonner renders the icon through `<component :is>`, so the three shapes
// beta.24's toast.create took have to arrive as components.
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

/**
 * `toast.create({ message, ... })` shape kept alive for customer-written form
 * scripts. frappe-ui v1 dropped `toast.create` for `toast(message, options)`.
 */
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
  let onChangeFieldMap = {};
  for (const script of scripts) {
    const parsed = await parseScript(script, obj);
    actions = actions.concat(parsed.actions);
    if (parsed.onChange) {
      parseOnChangeFn(onChangeFieldMap, parsed.onChange);
    }
  }
  data._customActions = withLegacyGroupOptions(actions);
  if (Object.keys(onChangeFieldMap).length) {
    data._customOnChange = onChangeFieldMap;
  }
}

// Form scripts written before frappe-ui v1 name a group's children `items`,
// which the menu no longer reads, so the whole group goes missing.
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
      onChange: formScript?.onChange || null,
    };
  } catch (error) {
    console.error(error);
    toast.error(__("A form script on this page failed to run"));
    return { actions: [], onChange: null };
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
