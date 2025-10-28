import { createSuggestionExtension } from "frappe-ui/src/components/TextEditor/extensions/suggestion/createSuggestionExtension";
import { PluginKey } from "@tiptap/pm/state";
import FieldAutocompleteList from "./FieldAutocompleteList.vue";
import { getMeta } from "@/stores/meta";
import { userFields } from "../cannedResponse";

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
        field.label.toLowerCase().includes(query.toLowerCase()) ||
        field.value.toLowerCase().includes(query.toLowerCase())
    );
  },
  command: ({ editor, range, props: item }) => {
    editor
      .chain()
      .focus()
      .deleteRange(range)
      .insertContent(`{{ ${item.value} }}`)
      .run();
  },
  component: FieldAutocompleteList,
});
