import { Extension } from "@tiptap/core";
import { createSuggestionExtension } from "frappe-ui";
import { PluginKey } from "@tiptap/pm/state";
import { getMeta } from "./stores/meta";
import { userFields } from "./components/Settings/SavedReplies/savedReplies";
import FieldAutocompleteList from "./components/Settings/SavedReplies/components/FieldAutocompleteList.vue";

export interface FieldItem {
  title: string;
  value: string;
}

export const FieldAutocompleteSuggestionKey = new PluginKey<any>(
  "fieldAutocomplete"
);

const ticketMeta = getMeta("HD Ticket");

export const FieldAutocomplete = createSuggestionExtension<FieldItem>({
  name: "fieldAutocomplete",
  char: "{{",
  allowSpaces: true,
  pluginKey: FieldAutocompleteSuggestionKey,
  items: ({ editor, query, ...rest }) => {
    // Return empty list to force the dropdown to close.
    if (query.includes("}}")) {
      return [];
    }

    // Clean up query when editing inside existing {{ }} brackets
    // Remove any trailing `}}` and trim whitespace
    const cleanedQuery = query.replace(/\s*}}.*$/, "").trim();

    const fields = ticketMeta
      .getFields()
      .filter(
        (f) =>
          f.fieldtype !== "Tab Break" &&
          f.fieldtype !== "Section Break" &&
          Boolean(f.label)
      )
      .map((f) => ({ label: f.label, value: f.fieldname }))
      .concat(userFields);

    return fields.filter(
      (field) =>
        field.label.toLowerCase().includes(cleanedQuery.toLowerCase()) ||
        field.value.toLowerCase().includes(cleanedQuery.toLowerCase())
    );
  },
  command: ({ editor, range, props: item }) => {
    const { state } = editor;
    const textAfterCursor = state.doc.textBetween(
      range.to,
      Math.min(range.to + 10, state.doc.content.size),
      ""
    );

    let extendedTo = range.to;
    const closingMatch = textAfterCursor.match(/^\s*}}/);
    if (closingMatch) {
      extendedTo = range.to + closingMatch[0].length;
    }

    editor
      .chain()
      .focus()
      .deleteRange({ from: range.from, to: extendedTo })
      .insertContent(`{{ ${item.value} }} `)
      .run();
  },
  component: FieldAutocompleteList,
});

export const PreserveVideoControls: Extension = Extension.create({
  name: "preserveVideoControls",
  addGlobalAttributes() {
    return [
      {
        types: ["video"],
        attributes: {
          controls: {
            default: true,
            parseHTML: (element) => element.getAttribute("controls"),
            renderHTML: () => {
              return { controls: true };
            },
          },
        },
      },
    ];
  },
});

export const PreserveIds: Extension = Extension.create({
  name: "preserveIds",
  addGlobalAttributes() {
    return [
      {
        types: ["heading"],
        attributes: {
          id: {
            default: null,
            parseHTML: (element) => element.getAttribute("id"),
            renderHTML: (attributes) => {
              if (!attributes.id) {
                return {};
              }
              return { id: attributes.id };
            },
          },
        },
      },
    ];
  },
});
