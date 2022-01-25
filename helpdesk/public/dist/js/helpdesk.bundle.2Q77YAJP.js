(()=>{window.FileAttachmentHandler=class{constructor(){this.add_attachment_handler(),this.set_listeners()}add_attachment_handler(){var t=this;$(".add-attachment-helpdesk").click(function(){t.new_attachment()})}new_attachment(){new frappe.ui.FileUploader({folder:"Home/Attachments",on_success:t=>{console.log(`File ${t.name} uploaded`),this.attachments||(this.attachments=[]),this.save_paths||(this.save_paths={}),this.attachments.push(t),$(".helpdesk-attachment").empty().append(this.build_attachment_table())}})}build_attachment_table(){console.log("Here 10");var t=$('<div class="helpdesk-attachment"></div>');t.empty();var n=$(this.get_attachment_table_header_html()).appendTo(t);return!this.attachments||!this.attachments.length?"No attachments uploaded":(this.attachments.forEach(e=>{let a=$("<tr></tr>").appendTo(n.find("tbody"));$(`<td>${e.file_name}</td>`).appendTo(a),$(`<td>
			<a class="btn btn-default btn-xs btn-primary-light text-nowrap copy-link" data-link="![](${e.file_url})" data-name = "${e.file_name}" >
				Copy Link
			</a>
			</td>`).appendTo(a),$(`<td>
			<a class="btn btn-default btn-xs  center delete-button"  data-name = "${e.file_name}" >
			<svg class="icon icon-sm"><use xlink:href="#icon-delete"></use></svg>
			</a>
			</td>`).appendTo(a)}),t)}get_attachment_table_header_html(){return`<table class="table  attachment-table" ">
			<tbody></tbody>
		</table>`}handle_attachment_upload_callback(t){this.attachments}set_listeners(){var t=this;$("body").on("click",".copy-link",function(){frappe.utils.copy_to_clipboard($(this).attr("data-link"))}),$("body").on("click",".delete-button",function(){frappe.confirm(`Are you sure you want to delete the file "${$(this).attr("data-name")}"`,()=>{t.attachments.forEach((n,e,a)=>{n.file_name==$(this).attr("data-name")&&a.splice(e,1)}),$(".helpdesk-attachment").empty().append(t.build_attachment_table())})})}};})();
//# sourceMappingURL=helpdesk.bundle.2Q77YAJP.js.map
