import { createResource } from "frappe-ui";
import { reactive } from "vue";

const doctypeMeta = reactive({});
const userSettings = reactive({});

export function getMeta(doctype: string) {
  const meta = createResource({
    url: "frappe.desk.form.load.getdoctype",
    params: {
      doctype: doctype,
      with_parent: 1,
      cached_timestamp: null,
    },
    cache: ["Meta", doctype],
    onSuccess: (res) => {
      let dtMetas = res.docs;
      for (let dtMeta of dtMetas) {
        doctypeMeta[dtMeta.name] = dtMeta;
      }

      userSettings[doctype] = JSON.parse(res.user_settings);
    },
  });
  if (!doctypeMeta[doctype] && !meta.loading) {
    meta.fetch();
  }
  function getFields(dt = null) {
    dt = dt || doctype;
    return doctypeMeta[dt]?.fields.map((f) => f) || [];
  }

  function getField(fieldname: string) {
    return (
      doctypeMeta[doctype]?.fields.find((f) => f.fieldname === fieldname) ||
      null
    );
  }

  return { meta, doctypeMeta, getField, getFields };
}
