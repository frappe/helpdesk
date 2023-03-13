window.FileAttachmentHandler = class FileAttachmentHandler {
	constructor() {
		this.add_attachment_handler()
		this.set_listeners()
	}

	add_attachment_handler() {
		var me = this
		$(".add-attachment-helpdesk").click(function () {
			me.new_attachment()
		})
	}

	new_attachment() {
		new frappe.ui.FileUploader({
			folder: "Home/Attachments",
			on_success: (file_doc) => {
				if (!this.attachments) this.attachments = []
				if (!this.save_paths) this.save_paths = {}
				this.attachments.push(file_doc)
				$(".helpdesk-attachment")
					.empty()
					.append(this.build_attachment_table())
				// $(".attachment-controls").find(".number").text(this.attachments.length);
			},
		})
	}

	build_attachment_table() {
		var wrapper = $('<div class="helpdesk-attachment"></div>')
		wrapper.empty()

		var table = $(this.get_attachment_table_header_html()).appendTo(wrapper)
		if (!this.attachments || !this.attachments.length)
			return "No attachments uploaded"

		this.attachments.forEach((f) => {
			const row = $("<tr></tr>").appendTo(table.find("tbody"))
			$(`<td>${f.file_name}</td>`).appendTo(row)
			$(`<td>
			<a class="btn btn-default btn-xs btn-primary-light text-nowrap copy-link" data-link="![](${f.file_url})" data-name = "${f.file_name}" >
				Copy Link
			</a>
			</td>`).appendTo(row)
			$(`<td>
			<a class="btn btn-default btn-xs  center delete-button"  data-name = "${f.file_name}" >
			<svg class="icon icon-sm"><use xlink:href="#icon-delete"></use></svg>
			</a>
			</td>`).appendTo(row)
		})
		return wrapper
	}

	get_attachment_table_header_html() {
		return `<table class="table  attachment-table" ">
			<tbody></tbody>
		</table>`
	}

	handle_attachment_upload_callback(method) {
		if (this.attachments) {
		}
	}

	set_listeners() {
		var me = this

		$(`body`).on("click", `.copy-link`, function () {
			frappe.utils.copy_to_clipboard($(this).attr("data-link"))
		})

		$(`body`).on("click", `.delete-button`, function () {
			frappe.confirm(
				`Are you sure you want to delete the file "${$(this).attr(
					"data-name"
				)}"`,
				() => {
					me.attachments.forEach((f, index, object) => {
						if (f.file_name == $(this).attr("data-name")) {
							object.splice(index, 1)
						}
					})
					$(".helpdesk-attachment")
						.empty()
						.append(me.build_attachment_table())
				}
			)
		})
	}
}
