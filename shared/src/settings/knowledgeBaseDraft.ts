import {
  call,
  createDocumentResource,
  createListResource,
  createResource,
  toast,
} from "frappe-ui";
import { computed, ref, shallowRef, watch } from "vue";
import { KB_PREVIEW_KEY, type KbPreview } from "../kbPreview";
import { __ } from "../translation";
import { CUSTOMER_PORTAL_ROOT, getErrorMessage, isSafeLink } from "../utils";

type Link = KbPreview["links"][number];

type Draft = KbPreview & {
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

// Quick links live in a knowledge base form script, the way field dependencies do; its last line holds the rows.
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
    fields: ["name", "category_name", "pinned"],
    orderBy: "category_name asc",
    pageLength: 999,
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

  const categoryOptions = computed(() =>
    (categories.data || []).map((row) => ({
      label: row.category_name,
      value: row.name,
    }))
  );

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

  async function savePinned(pinned: string[]) {
    const before = saved.value!.pinned;
    const { failed_docs } = await call("frappe.client.bulk_update", {
      docs: categoryOptions.value
        .map(({ value }) => value)
        .filter((name) => pinned.includes(name) !== before.includes(name))
        .map((name) => ({
          doctype: "HD Article Category",
          docname: name,
          pinned: pinned.includes(name) ? 1 : 0,
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
      localStorage.removeItem(KB_PREVIEW_KEY);
    } catch {}
  }

  function preview() {
    const { banner_image, banner_preset, pinned, links } = normalize(
      draft.value!
    );
    const look: KbPreview = { banner_image, banner_preset, pinned, links };
    localStorage.setItem(KB_PREVIEW_KEY, JSON.stringify(look));
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

// Trimmed, empty link rows dropped and pins sorted, so neither typing nor pick order counts as an edit.
function normalize(draft: Draft): Draft {
  return {
    ...draft,
    pinned: [...draft.pinned].sort(),
    links: draft.links
      .map(({ label, url, open_in_new_tab }) => ({
        label: label?.trim() || "",
        url: url?.trim() || "",
        open_in_new_tab: Boolean(open_in_new_tab),
      }))
      .filter((link) => link.label || link.url),
  };
}
