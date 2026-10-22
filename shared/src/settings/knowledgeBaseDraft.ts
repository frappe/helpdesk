import {
  call,
  createDocumentResource,
  createListResource,
  createResource,
  getCachedDocumentResource,
  toast,
} from "frappe-ui";
import { computed, effectScope, ref, shallowRef, watch } from "vue";
import {
  KNOWLEDGE_BASE_PREVIEW_KEY,
  type KnowledgeBasePreview,
} from "../knowledgeBasePreview";
import { __ } from "../translation";
import { CUSTOMER_PORTAL_ROOT, getErrorMessage, isSafeLink } from "../utils";

type Link = KnowledgeBasePreview["links"][number];

type Draft = KnowledgeBasePreview;

const SETTINGS_FIELDS = ["banner_image", "banner_preset"] as const;

// Quick links live in a form script; its last line holds them as JSON.
const LINKS_SCRIPT = "Knowledge Base Quick Links";
const JSON_MARKER = "//JSON: ";

// Only the last line: labels may contain the marker; hand edits may not parse.
function parseLinks(script: string): Link[] {
  const lastLine = script.trimEnd().split("\n").pop() || "";
  if (!lastLine.startsWith(JSON_MARKER)) return [];
  try {
    const links = JSON.parse(lastLine.slice(JSON_MARKER.length));
    return Array.isArray(links) ? links : [];
  } catch {
    return [];
  }
}

// Lazy singleton shared by desk and portal settings.
export const knowledgeBaseDraft = shallowRef<ReturnType<
  typeof createDraft
> | null>(null);

export function useKnowledgeBaseDraft() {
  // Detached: the singleton outlives the first form, so must its watchers.
  return (knowledgeBaseDraft.value ??= effectScope(true).run(createDraft)!);
}

function createDraft() {
  // Reuse: re-creating a cached doc refetches it.
  const settings =
    getCachedDocumentResource("HD Settings", "HD Settings") ||
    createDocumentResource({ doctype: "HD Settings", name: "HD Settings" });
  const categories = createListResource({
    doctype: "HD Article Category",
    fields: ["name", "category_name", "icon", "pinned", "pinned_order"],
    orderBy: "category_name asc",
    pageLength: 99999,
    auto: true,
  });
  const accessRows = createResource({
    url: "frappe.client.get_list",
    params: {
      doctype: "HD Article",
      fields: ["category", "visibility"],
      group_by: "category, visibility",
      order_by: "category asc",
      limit_page_length: 0,
    },
    auto: true,
  });
  const linksScript = createResource({
    url: "frappe.client.get_value",
    params: {
      doctype: "HD Form Script",
      filters: { name: LINKS_SCRIPT },
      fieldname: "script",
    },
    auto: true,
  });

  const saved = computed<Draft | null>(() => {
    if (!settings.doc || !categories.data || !linksScript.data) return null;
    const script: string = linksScript.data.script || "";
    return {
      banner_image: settings.doc.banner_image || "",
      banner_preset: settings.doc.banner_preset || "",
      pinned: categories.data
        .filter((row) => row.pinned)
        .sort((a, b) => a.pinned_order - b.pinned_order)
        .map((row) => row.name),
      links: parseLinks(script),
    };
  });

  // Track `saved` but keep unsaved edits: a pin save must not wipe them.
  const draft = ref<Draft | null>(null);
  watch(
    () => JSON.stringify(saved.value),
    (json, previous) => {
      const next = JSON.parse(json);
      const before = previous ? JSON.parse(previous) : null;
      if (next && before && draft.value) {
        const now = normalize(draft.value);
        const was = normalize(before);
        for (const key of Object.keys(next) as (keyof Draft)[]) {
          if (JSON.stringify(now[key]) !== JSON.stringify(was[key])) {
            next[key] = draft.value[key];
          }
        }
      }
      draft.value = next;
    },
    { immediate: true }
  );

  const categoryOptions = computed(() => {
    const access: Record<string, string> = {};
    for (const row of accessRows.data || []) {
      access[row.category] = access[row.category] ? "Mixed" : row.visibility;
    }
    // Customers never see Private categories; already pinned ones stay to unpin.
    return (categories.data || [])
      .filter((row) => access[row.name] !== "Private" || row.pinned)
      .map((row) => ({
        label: row.category_name,
        value: row.name,
        icon: row.icon?.startsWith("lucide-") ? row.icon : "lucide-folder",
        access: access[row.name],
      }));
  });

  const changed = computed(() => {
    if (!draft.value || !saved.value) return [];
    const now = normalize(draft.value);
    const before = normalize(saved.value);
    return Object.keys(now).filter(
      (key) => JSON.stringify(now[key]) !== JSON.stringify(before[key])
    );
  });
  const isDirty = computed(() => changed.value.length > 0);

  const saving = ref(false);

  async function save() {
    const value = normalize(draft.value!);
    if (value.links.some((link) => !link.label || !link.url)) {
      return toast.error(__("Each link needs a label and a URL"));
    }
    const unsafe = value.links.find((link) => !isSafeLink(link.url));
    if (unsafe) {
      return toast.error(
        __("{0}: use a web address, an email link or a path starting with /", [
          unsafe.label,
        ])
      );
    }
    saving.value = true;
    try {
      const fields = SETTINGS_FIELDS.filter((key) =>
        changed.value.includes(key)
      );
      if (fields.length) {
        await call("frappe.client.set_value", {
          doctype: "HD Settings",
          name: "HD Settings",
          fieldname: Object.fromEntries(fields.map((key) => [key, value[key]])),
        });
      }
      if (changed.value.includes("links")) await saveLinks(value.links);
      if (changed.value.includes("pinned")) await savePinned(value.pinned);
      clearPreview();
      await Promise.all([
        settings.reload(),
        linksScript.reload(),
        categories.reload(),
      ]);
      toast.success(__("Settings updated"));
      return true;
    } catch (error) {
      getErrorMessage(error, true);
    } finally {
      saving.value = false;
    }
  }

  // Order is 1-based; 0 means unpinned.
  async function savePinned(pinned: string[]) {
    const { failed_docs } = await call("frappe.client.bulk_update", {
      docs: categories.data
        .map((row) => ({ row, order: pinned.indexOf(row.name) + 1 }))
        .filter(
          ({ row, order }) =>
            Boolean(row.pinned) !== order > 0 || row.pinned_order !== order
        )
        .map(({ row, order }) => ({
          doctype: "HD Article Category",
          docname: row.name,
          pinned: order > 0 ? 1 : 0,
          pinned_order: order,
        })),
    });
    if (failed_docs.length) {
      throw new Error(__("Could not update the pinned categories"));
    }
  }

  function saveLinks(links: Link[]) {
    const json = JSON.stringify(links);
    const script = `function setupForm() {\n  return { links: ${json} };\n}\n${JSON_MARKER}${json}`;
    if (linksScript.data?.script) {
      return call("frappe.client.set_value", {
        doctype: "HD Form Script",
        name: LINKS_SCRIPT,
        fieldname: "script",
        value: script,
      });
    }
    return call("frappe.client.insert", {
      doc: {
        doctype: "HD Form Script",
        name: LINKS_SCRIPT,
        dt: "HD Ticket",
        apply_to_knowledge_base: 1,
        enabled: 1,
        script,
      },
    });
  }

  async function savePins(pinned: string[]) {
    try {
      await savePinned(pinned);
      // The merge watch keeps a draft that differs from the old saved order.
      draft.value!.pinned = [...pinned];
      await categories.reload();
      toast.success(__("Pinned categories updated"));
      return true;
    } catch (error) {
      getErrorMessage(error, true);
      return false;
    }
  }

  // Saves at once, bypassing the draft.
  function setToggle(fieldname: string, value: boolean) {
    settings.setValue.submit(
      { [fieldname]: value },
      { onSuccess: () => toast.success(__("Settings updated")) }
    );
  }

  function discard() {
    draft.value = JSON.parse(JSON.stringify(saved.value));
    clearPreview();
  }

  // Open preview tabs read this until it's removed.
  function clearPreview() {
    try {
      localStorage.removeItem(KNOWLEDGE_BASE_PREVIEW_KEY);
    } catch {}
  }

  function preview() {
    try {
      localStorage.setItem(
        KNOWLEDGE_BASE_PREVIEW_KEY,
        JSON.stringify(normalize(draft.value!))
      );
    } catch {
      return toast.error(__("Could not open the preview"));
    }
    window.open(`${CUSTOMER_PORTAL_ROOT}?preview=1`, "_blank");
  }

  return {
    draft,
    settings,
    setToggle,
    savePins,
    categoryOptions,
    isDirty,
    saving,
    save,
    discard,
    preview,
  };
}

// Ignore whitespace and empty link rows when diffing.
function normalize(draft: Draft): Draft {
  return {
    ...draft,
    links: draft.links
      .map(({ label, url, open_in_new_tab }) => ({
        label: label?.trim() || "",
        url: url?.trim() || "",
        open_in_new_tab: Boolean(open_in_new_tab),
      }))
      .filter((link) => link.label || link.url),
  };
}
