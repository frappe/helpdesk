import {
  call,
  createDocumentResource,
  createListResource,
  createResource,
  toast,
} from "frappe-ui";
import { computed, ref, shallowRef, watch } from "vue";
import {
  KNOWLEDGE_BASE_PREVIEW_KEY,
  type KnowledgeBasePreview,
} from "../knowledgeBasePreview";
import { __ } from "../translation";
import { CUSTOMER_PORTAL_ROOT, getErrorMessage, isSafeLink } from "../utils";

type Link = KnowledgeBasePreview["links"][number];

type Draft = KnowledgeBasePreview & {
  public_knowledge_base: boolean;
  allow_anonymous_article_voting: boolean;
};

const SETTINGS_FIELDS = [
  "public_knowledge_base",
  "allow_anonymous_article_voting",
  "banner_image",
  "banner_preset",
] as const;

const PREVIEW_FIELDS = ["banner_image", "banner_preset", "pinned", "links"];

// Quick links live in a knowledge base form script, the way field dependencies do: every
// customization is one kind of document, with no settings table of its own. Its last line holds the rows.
const LINKS_SCRIPT = "Knowledge Base Quick Links";
const JSON_MARKER = "//JSON: ";

// One draft for the desk and the portal settings, made on first use: the portal's header buttons read it
// before the form exists, and readers who never open the settings never load it.
export const knowledgeBaseDraft = shallowRef<ReturnType<
  typeof createDraft
> | null>(null);

export function useKnowledgeBaseDraft() {
  return (knowledgeBaseDraft.value ??= createDraft());
}

function createDraft() {
  const settings = createDocumentResource({
    doctype: "HD Settings",
    name: "HD Settings",
  });
  const categories = createListResource({
    doctype: "HD Article Category",
    fields: ["name", "category_name", "icon", "pinned", "pinned_order"],
    orderBy: "category_name asc",
    pageLength: 999,
    auto: true,
  });
  // Published article counts for the pinned list.
  const counts = createResource({
    url: "helpdesk.api.knowledge_base.get_categories",
    method: "GET",
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
      public_knowledge_base: Boolean(settings.doc.public_knowledge_base),
      allow_anonymous_article_voting: Boolean(
        settings.doc.allow_anonymous_article_voting
      ),
      banner_image: settings.doc.banner_image || "",
      banner_preset: settings.doc.banner_preset || "",
      pinned: categories.data
        .filter((row) => row.pinned)
        .sort((a, b) => a.pinned_order - b.pinned_order)
        .map((row) => row.name),
      links: script.includes(JSON_MARKER)
        ? JSON.parse(script.split(JSON_MARKER).pop()!)
        : [],
    };
  });

  const draft = ref<Draft | null>(null);
  watch(
    () => JSON.stringify(saved.value),
    (json) => (draft.value = JSON.parse(json)),
    { immediate: true }
  );

  const categoryOptions = computed(() => {
    const articleCounts = Object.fromEntries(
      (counts.data || []).map((row) => [row.name, row.article_count])
    );
    return (categories.data || []).map((row) => ({
      label: row.category_name,
      value: row.name,
      icon: row.icon?.startsWith("lucide-") ? row.icon : "lucide-folder",
      count: articleCounts[row.name] || 0,
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
  const canPreview = computed(() =>
    changed.value.some((key) => PREVIEW_FIELDS.includes(key))
  );

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
      if (changed.value.includes("pinned")) await savePinned(value.pinned);
      if (changed.value.includes("links")) await saveLinks(value.links);
      clearPreview();
      await Promise.all([
        settings.reload(),
        categories.reload(),
        linksScript.reload(),
      ]);
      toast.success(__("Settings updated"));
      return true;
    } catch (error) {
      getErrorMessage(error, true);
    } finally {
      saving.value = false;
    }
  }

  // A pin's position counts from 1; unpinned categories go back to 0.
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

  function discard() {
    draft.value = JSON.parse(JSON.stringify(saved.value));
  }

  // Preview tabs read the stored look until it's gone, so a save must not leave them on the old draft.
  function clearPreview() {
    try {
      localStorage.removeItem(KNOWLEDGE_BASE_PREVIEW_KEY);
    } catch {}
  }

  function preview() {
    const { banner_image, banner_preset, pinned, links } = normalize(
      draft.value!
    );
    const look: KnowledgeBasePreview = {
      banner_image,
      banner_preset,
      pinned,
      links,
    };
    localStorage.setItem(KNOWLEDGE_BASE_PREVIEW_KEY, JSON.stringify(look));
    window.open(`${CUSTOMER_PORTAL_ROOT}?preview=1`, "_blank");
  }

  return {
    draft,
    categoryOptions,
    isDirty,
    canPreview,
    saving,
    save,
    discard,
    preview,
  };
}

// Trimmed and empty link rows dropped, so typing alone doesn't count as an edit. Pin order does.
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
