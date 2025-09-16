import { Field } from "@/types";

export async function setupCustomizations(doc, obj) {
  // Supporting old format, will have to refactor later
  let data = doc.data ?? doc;
  if (!data) return;
  if (!data._form_script) return [];
  let actions = [];
  let onChangeFieldMap = {};
  if (Array.isArray(data._form_script)) {
    for (const script of data._form_script) {
      const parsed = await parseScript(script, obj);
      actions = actions.concat(parsed.actions);
      if (parsed.onChange) {
        parseOnChangeFn(onChangeFieldMap, parsed.onChange);
      }
    }
  } else {
    const parsed = await parseScript(data._form_script, obj);
    actions = parsed.actions;
    if (parsed.onChange) {
      parseOnChangeFn(onChangeFieldMap, parsed.onChange);
    }
  }
  data._customActions = actions;
  if (Object.keys(onChangeFieldMap).length) {
    data._customOnChange = onChangeFieldMap;
  }
}

function parseOnChangeFn(fieldMap: object, currentField: object) {
  for (const [key, value] of Object.entries(currentField)) {
    if (!fieldMap[key]) {
      fieldMap[key] = new Set();
    }
    fieldMap[key].add(value);
  }
}

async function parseScript(script, obj) {
  const scriptFn = new Function(script + "\nreturn setupForm")();
  const formScript = await scriptFn(obj);
  return {
    actions: formScript?.actions || [],
    onChange: formScript?.onChange || null,
  };
}

export function handleSelectFieldUpdate(
  f: Field,
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
  f: Field,
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

//
export function parseField(field, doc) {
  return {
    display_via_depends_on: evaluateDependsOnValue(field?.depends_on, doc),
    ...field,
    required:
      field.required ||
      (field.mandatory_depends_on &&
        evaluateDependsOnValue(field.mandatory_depends_on, doc)),
    filters: field.link_filters && JSON.parse(field.link_filters),
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
