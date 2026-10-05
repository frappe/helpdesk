import { parseLinkFilters } from "@helpdesk/shared/utils";

export {
  createToast,
  handleLinkFieldUpdate,
  handleSelectFieldUpdate,
  setupCustomizations,
} from "@helpdesk/shared/formScripts";

//
export function parseField(field, doc) {
  return {
    display_via_depends_on: evaluateDependsOnValue(field?.depends_on, doc),
    ...field,
    required:
      field.required ||
      (field.mandatory_depends_on &&
        evaluateDependsOnValue(field.mandatory_depends_on, doc)),
    filters: field.link_filters && parseLinkFilters(field.link_filters),
    disabled: field.disabled,
    readonly:
      field.readonly ||
      (field.read_only_depends_on &&
        evaluateDependsOnValue(field.read_only_depends_on, doc)),
  };
}

export function evaluateDependsOnValue(expression, doc) {
  if (!expression) return true;
  let out = null;
  if (expression.substr(0, 5) == "eval:") {
    try {
      out = _eval(expression.substr(5), { doc });
    } catch (e) {
      out = true;
    }
  } else if (expression.substr(0, 4) == "doc.") {
    out = doc[expression.substr(4)];
  } else {
    let value = doc[expression];
    if (Array.isArray(value)) {
      out = !!value.length;
    } else {
      out = !!value;
    }
  }
  return out;
}
function _eval(code, context = {}) {
  let variable_names = Object.keys(context);
  let variables = Object.values(context);
  code = `let out = ${code}; return out`;
  try {
    let expression_function = new Function(...variable_names, code);
    return expression_function(...variables);
  } catch (error) {
    console.log("Error evaluating the following expression:");
    console.error(code);
    throw error;
  }
}
