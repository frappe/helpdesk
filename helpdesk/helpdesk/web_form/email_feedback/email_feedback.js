frappe.ready(function () {
  let key = frappe.utils.get_url_arg("key");
  let web_form_doc = frappe.web_form_doc;
  frappe.web_form.set_value("key", key);
  setTimeout(() => {
    window.history.replaceState(null, null, window.location.pathname);
  }, 0);
});
