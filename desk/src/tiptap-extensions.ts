import { Extension, generateJSON } from "@tiptap/core";
import { Table, TableRow, TableCell, TableHeader } from '@tiptap/extension-table'
import { TextAlign } from "@tiptap/extension-text-align";
import { TextStyle } from "@tiptap/extension-text-style";
import { Plugin, PluginKey, TextSelection } from "@tiptap/pm/state";
import StarterKit from "@tiptap/starter-kit";
import { createSuggestionExtension } from "frappe-ui";
import FieldAutocompleteList from "./components/Settings/SavedReplies/components/FieldAutocompleteList.vue";
import { userFields } from "./components/Settings/SavedReplies/savedReplies";
import { getMeta } from "./stores/meta";

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

export const ComponentUtils: Extension = Extension.create({
  name: "ComponentUtils",
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
      {
        types: ["paragraph"],
        attributes: {
          class: {
            default: null,
            parseHTML: (element) => element.getAttribute("class"),
            renderHTML: (attributes) => {
              if (!attributes.class) return {};
              return { class: attributes.class };
            },
          },
        },
      },
      {
        types: ["table"],
        attributes: {
          style: {
            default: null,
            parseHTML: (el) => el.getAttribute("style"),
            renderHTML: () => ({
              style:
                "border-collapse: collapse; width: 100%; border: 1px solid #d1d5db;",
            }),
          },
        },
      },

      {
        types: ["tableRow"],
        attributes: {
          style: {
            default: null,
            parseHTML: (el) => el.getAttribute("style"),
            renderHTML: () => ({ style: "border: 1px solid #d1d5db;" }),
          },
        },
      },

      {
        types: ["tableCell", "tableHeader"],
        attributes: {
          style: {
            default: null,
            parseHTML: (el) => el.getAttribute("style"),
            renderHTML: () => ({
              style:
                "border: 1px solid #d1d5db; padding: 6px 8px; vertical-align: top; text-align: left;",
            }),
          },
        },
      },
    ];
  },
});

// The extensions that match frappe-ui's TextEditor schema, used for generateJSON
const excelPasteExtensions = [
  StarterKit,
  Table,
  TableRow,
  TableHeader,
  TableCell,
  TextStyle,
  TextAlign.configure({ types: ["heading", "paragraph"] }),
];

// Parsed per-element style info extracted from iframe computed styles
interface ElementStyles {
  fontWeight: string;
  fontStyle: string;
  textDecoration: string;
  color: string;
  backgroundColor: string;
  textAlign: string;
  fontSize: string;
  verticalAlign: string;
  whiteSpace: string;
}

interface TableCellMeta {
  colspan: number;
  rowspan: number;
  colwidth?: number[];
}

interface ResolvedExcelPaste {
  html: string;
  stylesByCell: Map<string, ElementStyles>;
  cellMetaByCell: Map<string, TableCellMeta>;
}

const DEFAULT_TEXT_COLORS = new Set([
  "rgb(0, 0, 0)",
  "rgba(0, 0, 0, 0)",
  "canvastext",
]);

const DEFAULT_BACKGROUND_COLORS = new Set([
  "rgba(0, 0, 0, 0)",
  "rgb(255, 255, 255)",
  "transparent",
]);

function convertExcelWidthToPx(width: string | null): number | null {
  if (!width) return null;

  const normalizedWidth = width.trim().toLowerCase();
  const match = normalizedWidth.match(/^([\d.]+)\s*(pt|px)?$/);
  if (!match) return null;

  const value = parseFloat(match[1]);
  if (!Number.isFinite(value) || value <= 0) return null;

  const unit = match[2] || "px";
  if (unit === "pt") {
    return Math.round(value * 1.333);
  }

  return Math.round(value);
}

function normalizeCellKey(rowIdx: number, colIdx: number) {
  return `r${rowIdx}:c${colIdx}`;
}

function isDefaultTextColor(color: string) {
  return DEFAULT_TEXT_COLORS.has(color.trim().toLowerCase());
}

function isDefaultBackgroundColor(color: string) {
  return DEFAULT_BACKGROUND_COLORS.has(color.trim().toLowerCase());
}

function sanitizeCssColor(color: string) {
  return color.trim().toLowerCase();
}

function applyInlineTextStyles(
  doc: Document,
  iframeWindow: Window,
  root: HTMLElement
) {
  const elements = Array.from(root.querySelectorAll("*")) as HTMLElement[];

  elements.forEach((element) => {
    if (
      ["TABLE", "TBODY", "THEAD", "TR", "TD", "TH"].includes(element.tagName)
    ) {
      return;
    }

    const computed = iframeWindow.getComputedStyle(element);
    const styleParts: string[] = [];

    const color = sanitizeCssColor(computed.color);
    if (!isDefaultTextColor(color)) {
      styleParts.push(`color: ${computed.color}`);
    }

    const backgroundColor = sanitizeCssColor(computed.backgroundColor);
    if (!isDefaultBackgroundColor(backgroundColor)) {
      styleParts.push(`background-color: ${computed.backgroundColor}`);
    }

    if (
      computed.fontSize &&
      computed.fontSize !== "14.6667px" &&
      computed.fontSize !== "16px"
    ) {
      styleParts.push(`font-size: ${computed.fontSize}`);
    }

    if (styleParts.length) {
      const existingStyle = element.getAttribute("style");
      element.setAttribute(
        "style",
        [existingStyle, ...styleParts].filter(Boolean).join("; ")
      );
    }
  });
}

function preserveWhitespaceAndBreaks(doc: Document, el: HTMLElement) {
  const walker = doc.createTreeWalker(el, NodeFilter.SHOW_TEXT);
  const textNodes: Text[] = [];

  while (walker.nextNode()) {
    textNodes.push(walker.currentNode as Text);
  }

  textNodes.forEach((textNode) => {
    const value = textNode.nodeValue;
    if (!value || !/[\n\t]| {2,}/.test(value)) return;

    const fragment = doc.createDocumentFragment();
    const parts = value.split(/(\n|\t| {2,})/g).filter(Boolean);

    parts.forEach((part) => {
      if (part === "\n") {
        fragment.appendChild(doc.createElement("br"));
        return;
      }

      if (part === "\t") {
        fragment.appendChild(doc.createTextNode("    "));
        return;
      }

      if (/^ {2,}$/.test(part)) {
        fragment.appendChild(doc.createTextNode(" "));
        for (let i = 1; i < part.length; i++) {
          fragment.appendChild(doc.createTextNode("\u00a0"));
        }
        return;
      }

      fragment.appendChild(doc.createTextNode(part));
    });

    textNode.parentNode?.replaceChild(fragment, textNode);
  });
}

function addMarkIfMissing(
  node: any,
  type: string,
  attrs?: Record<string, any>
) {
  const marks = [...(node.marks || [])];
  const existingMark = marks.find((mark) => mark.type === type);

  if (existingMark) {
    if (attrs) {
      existingMark.attrs = { ...(existingMark.attrs || {}), ...attrs };
    }
    return marks;
  }

  marks.push(attrs ? { type, attrs } : { type });
  return marks;
}

// Use the browser's CSSOM to fully resolve all computed styles on Excel HTML elements.
// Excel uses stylesheet classes (.xl65 etc.), not inline styles, so DOMParser alone
// cannot resolve them — we need a live document with the <style> block applied.
// Styles are keyed by "r{rowIdx}:c{colIdx}" for table cells so they survive DOM mutations.
async function resolveExcelStyles(html: string): Promise<ResolvedExcelPaste> {
  return new Promise((resolve) => {
    const iframe = document.createElement("iframe");
    iframe.style.cssText =
      "position:fixed;top:-9999px;left:-9999px;width:2000px;height:2000px;visibility:hidden;";
    document.body.appendChild(iframe);

    const iframeDoc = iframe.contentDocument!;
    iframeDoc.open();
    iframeDoc.write(html);
    iframeDoc.close();

    requestAnimationFrame(() => {
      const body = iframeDoc.body;
      // Key: "r{rowIdx}:c{colIdx}", value: computed styles for that cell
      const stylesByCell = new Map<string, ElementStyles>();
      const cellMetaByCell = new Map<string, TableCellMeta>();

      // Capture styles keyed by stable table coordinates
      iframeDoc.querySelectorAll("tr").forEach((tr, rowIdx) => {
        (tr as HTMLElement)
          .querySelectorAll("td, th")
          .forEach((cell, colIdx) => {
            const el = cell as HTMLElement;
            const computed = iframe.contentWindow!.getComputedStyle(el);
            const cellKey = normalizeCellKey(rowIdx, colIdx);
            stylesByCell.set(cellKey, {
              fontWeight: computed.fontWeight,
              fontStyle: computed.fontStyle,
              textDecoration:
                computed.textDecorationLine || computed.textDecoration,
              color: computed.color,
              backgroundColor: computed.backgroundColor,
              textAlign: computed.textAlign,
              fontSize: computed.fontSize,
              verticalAlign: computed.verticalAlign,
              whiteSpace: computed.whiteSpace,
            });

            const colspan =
              parseInt(el.getAttribute("colspan") || "1", 10) || 1;
            const rowspan =
              parseInt(el.getAttribute("rowspan") || "1", 10) || 1;
            cellMetaByCell.set(cellKey, {
              colspan,
              rowspan,
            });
          });
      });

      // Wrap cell contents with semantic tags based on cell-level computed styles
      iframeDoc.querySelectorAll("tr").forEach((tr, rowIdx) => {
        (tr as HTMLElement)
          .querySelectorAll("td, th")
          .forEach((cell, colIdx) => {
            const el = cell as HTMLElement;
            const s = stylesByCell.get(normalizeCellKey(rowIdx, colIdx));
            if (!s) return;
            if (parseInt(s.fontWeight) >= 700)
              wrapChildren(iframeDoc, el, "strong");
            if (s.fontStyle === "italic") wrapChildren(iframeDoc, el, "em");
            if (s.textDecoration?.includes("underline"))
              wrapChildren(iframeDoc, el, "u");
            if (s.textDecoration?.includes("line-through"))
              wrapChildren(iframeDoc, el, "s");

            applyInlineTextStyles(iframeDoc, iframe.contentWindow!, el);
            preserveWhitespaceAndBreaks(iframeDoc, el);
          });
      });

      // Remove CSS classes and <style> block so generateJSON sees clean HTML
      body.querySelectorAll("*").forEach((el) => el.removeAttribute("class"));
      iframeDoc.querySelectorAll("style").forEach((s) => s.remove());

      const resultHTML = body.innerHTML;
      document.body.removeChild(iframe);
      resolve({ html: resultHTML, stylesByCell, cellMetaByCell });
    });
  });
}

function wrapChildren(doc: Document, el: HTMLElement, tag: string) {
  if (
    el.children.length === 1 &&
    el.children[0].tagName.toLowerCase() === tag
  ) {
    return;
  }
  const wrapper = doc.createElement(tag);
  while (el.firstChild) {
    wrapper.appendChild(el.firstChild);
  }
  el.appendChild(wrapper);
}

// Post-process Tiptap JSON to inject textStyle marks (color, fontSize, backgroundColor)
// and paragraph attrs (textAlign) that generateJSON cannot infer from semantic HTML alone.
// stylesByCell is keyed "r{rowIdx}:c{colIdx}" matching table structure.
function injectStylesIntoJSON(
  json: any,
  stylesByCell: Map<string, ElementStyles>,
  cellMetaByCell: Map<string, TableCellMeta>
): any {
  function injectIntoNode(node: any, elStyle: ElementStyles | null): any {
    if (!elStyle) return node;

    if (node.type === "text") {
      const marks = [...(node.marks || [])];
      const textStyleAttrs: Record<string, string> = {};

      // Only apply non-default colors
      if (
        elStyle.color &&
        !isDefaultTextColor(sanitizeCssColor(elStyle.color))
      ) {
        textStyleAttrs.color = elStyle.color;
      }
      if (
        elStyle.backgroundColor &&
        !isDefaultBackgroundColor(sanitizeCssColor(elStyle.backgroundColor))
      ) {
        textStyleAttrs.backgroundColor = elStyle.backgroundColor;
      }
      if (
        elStyle.fontSize &&
        elStyle.fontSize !== "14.6667px" &&
        elStyle.fontSize !== "16px"
      ) {
        textStyleAttrs.fontSize = elStyle.fontSize;
      }

      if (Object.keys(textStyleAttrs).length > 0) {
        const existingTextStyle = marks.find((m) => m.type === "textStyle");
        if (existingTextStyle) {
          existingTextStyle.attrs = {
            ...existingTextStyle.attrs,
            ...textStyleAttrs,
          };
        } else {
          marks.push({ type: "textStyle", attrs: textStyleAttrs });
        }
      }

      if (elStyle.textDecoration?.includes("line-through")) {
        const strikeMarks = addMarkIfMissing({ marks }, "strike");
        return strikeMarks.length ? { ...node, marks: strikeMarks } : node;
      }

      return marks.length ? { ...node, marks } : node;
    }

    if (node.type === "paragraph") {
      const align = elStyle.textAlign;
      if (align === "right" || align === "center" || align === "justify") {
        node = { ...node, attrs: { ...node.attrs, textAlign: align } };
      }
    }

    if (node.content) {
      return {
        ...node,
        content: node.content.map((child: any) =>
          injectIntoNode(child, elStyle)
        ),
      };
    }

    return node;
  }

  // Walk table cells and inject styles per cell using row/col coordinates
  function walkNode(node: any): any {
    if (node.type === "table") {
      return {
        ...node,
        content: (node.content || []).map((row: any, rowIdx: number) => {
          if (row.type !== "tableRow") return row;
          return {
            ...row,
            content: (row.content || []).map((cell: any, colIdx: number) => {
              const cellKey = normalizeCellKey(rowIdx, colIdx);
              const elStyle = stylesByCell.get(cellKey) ?? null;
              const cellMeta = cellMetaByCell.get(cellKey);
              return {
                ...cell,
                attrs: {
                  ...cell.attrs,
                  ...(cellMeta?.colspan && cellMeta.colspan > 1
                    ? { colspan: cellMeta.colspan }
                    : {}),
                  ...(cellMeta?.rowspan && cellMeta.rowspan > 1
                    ? { rowspan: cellMeta.rowspan }
                    : {}),
                  ...(cellMeta?.colwidth?.length
                    ? { colwidth: cellMeta.colwidth }
                    : {}),
                },
                content: (cell.content || []).map((child: any) =>
                  injectIntoNode(child, elStyle)
                ),
              };
            }),
          };
        }),
      };
    }

    if (node.content) {
      return { ...node, content: node.content.map(walkNode) };
    }
    return node;
  }

  return { ...json, content: (json.content || []).map(walkNode) };
}

// Handle pasting from excel properly
export const HandleExcelPaste = Extension.create({
  name: "handleExcelPaste",

  addProseMirrorPlugins() {
    return [
      new Plugin({
        key: new PluginKey("handleExcelPaste"),
        props: {
          handlePaste(view, event) {
            const clipboardData = event.clipboardData;
            if (!clipboardData) return false;

            const types = Array.from(clipboardData.types);
            const hasFile = types.includes("Files");
            const hasHtml = types.includes("text/html");
            const hasText = types.includes("text/plain");
            const hasRtf = types.includes("text/rtf");

            if (hasFile && hasHtml && hasText && hasRtf) {
              event.preventDefault();
              const html = clipboardData.getData("text/html");
              const text = clipboardData.getData("text/plain");

              if (!html) {
                view.pasteText(text);
                return true;
              }

              // Async: use iframe + getComputedStyle to fully resolve Excel CSS classes,
              // then insert the enriched content into the editor
              resolveExcelStyles(html).then(
                ({ html: normalizedHTML, stylesByCell, cellMetaByCell }) => {
                  // Extract column widths from <col> elements (pt → px)
                  const tempDoc = new DOMParser().parseFromString(
                    html,
                    "text/html"
                  );
                  const colWidths: number[] = [];
                  tempDoc.querySelectorAll("col").forEach((col) => {
                    const span = parseInt(col.getAttribute("span") || "1", 10);
                    const styleWidth =
                      (col.getAttribute("style") || "").match(
                        /width:\s*([\d.]+(?:pt|px)?)/i
                      )?.[1] ?? null;
                    const widthPx =
                      convertExcelWidthToPx(styleWidth) ??
                      convertExcelWidthToPx(col.getAttribute("width"));
                    for (let i = 0; i < span; i++) {
                      colWidths.push(widthPx || 100);
                    }
                  });

                  let json = generateJSON(normalizedHTML, excelPasteExtensions);

                  // Inject colors, fontSize, textAlign from computed styles
                  json = injectStylesIntoJSON(
                    json,
                    stylesByCell,
                    cellMetaByCell
                  );

                  // Inject colwidth into each tableCell based on its column index
                  if (colWidths.length) {
                    (json.content || []).forEach((node: any) => {
                      if (node.type !== "table") return;
                      (node.content || []).forEach((row: any) => {
                        if (row.type !== "tableRow") return;
                        (row.content || []).forEach(
                          (cell: any, colIdx: number) => {
                            if (
                              cell.type !== "tableCell" &&
                              cell.type !== "tableHeader"
                            )
                              return;
                            const span = cell.attrs?.colspan || 1;
                            const widths = colWidths.slice(
                              colIdx,
                              colIdx + span
                            );
                            const widthValues = widths.filter(Boolean);
                            if (widthValues.length) {
                              cell.attrs = {
                                ...cell.attrs,
                                colwidth: widthValues,
                              };
                            }
                          }
                        );
                      });
                    });
                  }

                  const { state, dispatch } = view;
                  const { tr, selection, schema } = state;
                  const nodes = (json.content || [])
                    .map((n: any) => {
                      try {
                        return schema.nodeFromJSON(n);
                      } catch {
                        return null;
                      }
                    })
                    .filter(Boolean);

                  if (!nodes.length) return;
                  let totalInsertedSize = 0;
                  nodes.forEach((n: any) => {
                    totalInsertedSize += n.nodeSize;
                  });

                  const insertTr = tr.replaceWith(
                    selection.from,
                    selection.to,
                    nodes
                  );
                  dispatch(insertTr);

                  // After the table is inserted, ensure there is a paragraph after it
                  // and move the cursor there. We do this in a separate transaction so
                  // we can walk the already-updated document and find the exact node
                  // position after the last inserted top-level node.
                  requestAnimationFrame(() => {
                    const currentState = view.state;
                    const followUpTr = currentState.tr;

                    // Walk top-level nodes to find the end of the inserted block.
                    let tableEnd: number | null = null;
                    let offset = 0;
                    currentState.doc.forEach((node, nodeOffset) => {
                      if (
                        nodeOffset >= selection.from &&
                        nodeOffset < selection.from + totalInsertedSize
                      ) {
                        tableEnd = nodeOffset + node.nodeSize;
                      }
                      offset = nodeOffset;
                    });

                    if (tableEnd === null) return;

                    // If nothing exists after the table, insert an empty paragraph.
                    const needsParagraph =
                      tableEnd >= currentState.doc.content.size;
                    if (needsParagraph) {
                      followUpTr.insert(
                        currentState.doc.content.size,
                        currentState.schema.nodes.paragraph.create()
                      );
                    }

                    // Resolve the position just inside the paragraph after the table.
                    const targetPos = Math.min(
                      tableEnd + 1,
                      followUpTr.doc.content.size - 1
                    );
                    const $target = followUpTr.doc.resolve(targetPos);
                    followUpTr.setSelection(TextSelection.near($target, 1));
                    followUpTr.scrollIntoView();
                    view.dispatch(followUpTr);
                  });
                }
              );

              return true;
            }

            return false;
          },
        },
      }),
    ];
  },
});
