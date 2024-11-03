import { Extension } from "@tiptap/core";

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
