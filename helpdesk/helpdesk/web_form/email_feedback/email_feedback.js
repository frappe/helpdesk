frappe.ready(function () {
  let key = frappe.utils.get_url_arg("key");
  console.log("Key from URL:", key);
  if (!key) return;
});
