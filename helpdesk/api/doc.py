import frappe
from frappe import _
from frappe.model import no_value_fields
from frappe.model.document import get_controller
from frappe.utils.caching import redis_cache
from pypika import Criterion

from helpdesk.utils import check_permissions


@frappe.whitelist()
def get_list_data(
    doctype: str,
    # flake8: noqa
    filters={},
    default_filters={},
    order_by: str = "modified desc",
    page_length=20,
    columns=None,
    rows=None,
    show_customer_portal_fields=False,
    view=None,
    is_default=False,
):
    is_custom = False

    rows = frappe.parse_json(rows or "[]")
    columns = frappe.parse_json(columns or "[]")
    filters = frappe.parse_json(filters or "[]")

    view_type = view.get("view_type") if view else None
    view_name = view.get("name") if view else None

    group_by_field = view.get("group_by_field") if view else None
    label_doc = view.get("label_doc") if view else None
    label_field = view.get("label_field") if view else None

    handle_at_me_support(filters)

    if doctype == "HD Ticket" and not show_customer_portal_fields:
        handle_team_restrictions(filters)

    _list = get_controller(doctype)
    default_rows = []
    if hasattr(_list, "default_list_data"):
        default_rows = _list.default_list_data().get("rows")

    if columns or rows:
        is_default = False
        is_custom = True
        columns = frappe.parse_json(columns)
        rows = frappe.parse_json(rows)

    if not columns:
        columns = [
            {"label": "Name", "type": "Data", "key": "name", "width": "16rem"},
            {
                "label": "Last Modified",
                "type": "Datetime",
                "key": "modified",
                "width": "8rem",
            },
        ]

    if not rows:
        rows = ["name"]

    # flake8: noqa
    if is_default:
        default_view = default_view_exists(doctype)
        if not default_view:
            if hasattr(_list, "default_list_data"):
                columns = (
                    _list.default_list_data(show_customer_portal_fields).get("columns")
                    if doctype == "HD Ticket"
                    else _list.default_list_data().get("columns")
                )
                rows = default_rows
        else:
            [columns, rows] = handle_default_view(
                doctype, _list, show_customer_portal_fields
            )
            if default_filters and not filters:
                filters.append(default_filters)

    if rows is None:
        rows = []

    # check if rows has all keys from columns if not add them
    for column in columns:
        if column.get("key") not in rows:
            rows.append(column.get("key"))

    if group_by_field and group_by_field not in rows:
        rows.append(group_by_field)

    rows.append("name") if "name" not in rows else rows
    data = (
        frappe.get_list(
            doctype,
            fields=rows,
            filters=filters,
            order_by=order_by,
            page_length=page_length,
        )
        or []
    )

    fields = frappe.get_meta(doctype).fields
    fields = [field for field in fields if field.fieldtype not in no_value_fields]
    fields = [
        {
            "label": field.label,
            "type": field.fieldtype,
            "value": field.fieldname,
            "options": field.options,
        }
        for field in fields
        if field.label and field.fieldname
    ]

    std_fields = [
        {"label": "Name", "type": "Data", "value": "name"},
        {"label": "Created On", "type": "Datetime", "value": "creation"},
        {"label": "Last Modified", "type": "Datetime", "value": "modified"},
        {
            "label": "Modified By",
            "type": "Link",
            "value": "modified_by",
            "options": "User",
        },
        {"label": "Assigned To", "type": "Text", "value": "_assign"},
        {"label": "Owner", "type": "Link", "value": "owner", "options": "User"},
    ]

    for field in std_fields:
        if field.get("value") not in rows:
            rows.append(field.get("value"))
        if field not in fields:
            fields.append(field)

    if show_customer_portal_fields:
        fields = get_customer_portal_fields(doctype, fields)

    if group_by_field and view_type == "group_by":

        def get_options(fieldtype, options):
            if fieldtype == "Select":
                return [option for option in options.split("\n")]
            else:
                has_empty_values = any([not d.get(group_by_field) for d in data])
                options = list(set([d.get(group_by_field) for d in data]))
                options = [u for u in options if u]
                options = [category_name for category_name in options if category_name]
                options = [
                    {
                        "label": frappe.db.get_value(
                            label_doc if label_doc else doctype,
                            option,
                            label_field if label_field else group_by_field,
                        ),
                        "value": option,
                    }
                    for option in options
                    if option
                ]
                if has_empty_values:
                    options.append({"label": "", "value": ""})

                if order_by and group_by_field in order_by:
                    order_by_fields = order_by.split(",")
                    order_by_fields = [
                        (field.split(" ")[0], field.split(" ")[1])
                        for field in order_by_fields
                    ]
                    if (group_by_field, "asc") in order_by_fields:
                        options.sort(key=lambda x: x.get("label"))
                    elif (group_by_field, "desc") in order_by_fields:
                        options.sort(reverse=True, key=lambda x: x.get("label"))
                else:
                    options.sort(key=lambda x: x.get("label"))

                # general category at first position
                idx = [
                    idx for idx, o in enumerate(options) if o.get("label") == "General"
                ]
                if len(idx) == 0:
                    return options

                idx = idx[0]
                default_category = options[idx]
                options.pop(idx)
                options.insert(0, default_category)
                return options

        for field in fields:
            if field.get("value") == group_by_field:
                options = get_options(field.get("type"), field.get("options"))
                group_by_field = {
                    "label": field.get("label"),
                    "name": field.get("value"),
                    "type": field.get("type"),
                    "options": options,
                }
    return {
        "data": data,
        "columns": columns,
        "rows": rows,
        "fields": fields if doctype == "HD Ticket" else [],
        "total_count": frappe.get_list(
            doctype, filters=filters, fields="count(*) as count"
        )[0].count,
        "row_count": len(data),
        "group_by_field": group_by_field,
        "view_type": view_type,
    }


@frappe.whitelist()
@redis_cache()
def get_filterable_fields(doctype: str, show_customer_portal_fields=False):
    check_permissions(doctype, None)
    QBDocField = frappe.qb.DocType("DocField")
    QBCustomField = frappe.qb.DocType("Custom Field")
    allowed_fieldtypes = [
        "Check",
        "Data",
        "Float",
        "Int",
        "Link",
        "Long Text",
        "Select",
        "Small Text",
        "Text Editor",
        "Text",
        "Rating",
        "Duration",
        "Date",
        "Datetime",
    ]

    visible_custom_fields = get_visible_custom_fields()
    customer_portal_fields = [
        "name",
        "subject",
        "status",
        "priority",
        "response_by",
        "resolution_by",
        "creation",
    ]

    from_doc_fields = (
        frappe.qb.from_(QBDocField)
        .select(
            QBDocField.fieldname,
            QBDocField.fieldtype,
            QBDocField.label,
            QBDocField.name,
            QBDocField.options,
        )
        .where(QBDocField.parent == doctype)
        .where(QBDocField.hidden == False)
        .where(Criterion.any([QBDocField.fieldtype == i for i in allowed_fieldtypes]))
    )

    from_custom_fields = (
        frappe.qb.from_(QBCustomField)
        .select(
            QBCustomField.fieldname,
            QBCustomField.fieldtype,
            QBCustomField.label,
            QBCustomField.name,
            QBCustomField.options,
        )
        .where(QBCustomField.dt == doctype)
        .where(QBCustomField.hidden == False)
        .where(
            Criterion.any([QBCustomField.fieldtype == i for i in allowed_fieldtypes])
        )
    )

    # for customer portal show only fields present in customer_portal_fields
    if show_customer_portal_fields:
        from_doc_fields = from_doc_fields.where(
            QBDocField.fieldname.isin(customer_portal_fields)
        )
        if len(visible_custom_fields) > 0:
            from_custom_fields = from_custom_fields.where(
                QBCustomField.fieldname.isin(visible_custom_fields)
            )
            from_custom_fields = from_custom_fields.run(as_dict=True)
        else:
            from_custom_fields = []

    if not show_customer_portal_fields:
        from_custom_fields = from_custom_fields.run(as_dict=True)

    from_doc_fields = from_doc_fields.run(as_dict=True)
    # from hd ticket template get children with fieldname and hidden_from_customer

    res = []
    res.extend(from_doc_fields)
    # TODO: Ritvik => till a better way we have for custom fields, just show custom fields

    res.extend(from_custom_fields)
    if not show_customer_portal_fields and doctype == "HD Ticket":
        res.append(
            {
                "fieldname": "_assign",
                "fieldtype": "Link",
                "label": "Assigned to",
                "name": "_assign",
                "options": "HD Agent",
            }
        )

    enable_restrictions = frappe.db.get_single_value(
        "HD Settings", "restrict_tickets_by_agent_group"
    )
    if enable_restrictions and doctype == "HD Ticket":
        res = [r for r in res if r.get("fieldname") != "agent_group"]

    standard_fields = [
        {"fieldname": "name", "fieldtype": "Link", "label": "ID", "options": doctype},
        {
            "fieldname": "owner",
            "fieldtype": "Link",
            "label": "Created By",
            "options": "User",
        },
        {
            "fieldname": "modified_by",
            "fieldtype": "Link",
            "label": "Last Updated By",
            "options": "User",
        },
        {"fieldname": "creation", "fieldtype": "Datetime", "label": "Created On"},
        {"fieldname": "modified", "fieldtype": "Datetime", "label": "Last Updated On"},
    ]
    for field in standard_fields:
        if field.get("fieldname") not in [r.get("fieldname") for r in res]:
            res.append(field)
    return res


@frappe.whitelist()
def sort_options(doctype: str, show_customer_portal_fields=False):
    fields = frappe.get_meta(doctype).fields
    fields = [field for field in fields if field.fieldtype not in no_value_fields]
    fields = [
        {
            "label": field.label,
            "value": field.fieldname,
        }
        for field in fields
        if field.label and field.fieldname
    ]

    if show_customer_portal_fields:
        fields = get_customer_portal_fields(doctype, fields)

    standard_fields = [
        {"label": "Name", "value": "name"},
        {"label": "Created On", "value": "creation"},
        {"label": "Last Modified", "value": "modified"},
        {"label": "Modified By", "value": "modified_by"},
        {"label": "Owner", "value": "owner"},
    ]

    fields.extend(standard_fields)

    return fields


@frappe.whitelist()
def get_quick_filters(doctype: str, show_customer_portal_fields=False):
    meta = frappe.get_meta(doctype)
    fields = [field for field in meta.fields if field.in_standard_filter]
    quick_filters = []
    name_filter = {"label": "ID", "name": "name", "type": "Data"}
    if doctype == "Contact":
        quick_filters.append(name_filter)
        return quick_filters
    name_filter_doctypes = ["HD Agent", "HD Customer", "HD Ticket"]
    if doctype in name_filter_doctypes:
        quick_filters.append(name_filter)

    for field in fields:
        options = []
        if field.fieldtype == "Select":
            options = field.options.split("\n")
            options = [{"label": option, "value": option} for option in options]
            options.insert(0, {"label": "", "value": ""})

        if field.fieldtype == "Link":
            options = field.options

        quick_filters.append(
            {
                "label": _(field.label),
                "name": field.fieldname,
                "type": field.fieldtype,
                "options": options,
            }
        )

    if doctype != "HD Ticket":
        return quick_filters

    _list = get_controller(doctype)
    if hasattr(_list, "filter_standard_fields") and show_customer_portal_fields:
        # to filter out more fields from customer remember to update customer_not_allowed_fields in hd_ticket.py
        quick_filters = _list.filter_standard_fields(quick_filters)

    return quick_filters


def get_customer_portal_fields(doctype, fields):
    visible_custom_fields = get_visible_custom_fields()
    customer_portal_fields = [
        "name",
        "subject",
        "status",
        "priority",
        "response_by",
        "resolution_by",
        "creation",
        *visible_custom_fields,
    ]
    fields = [field for field in fields if field.get("value") in customer_portal_fields]
    return fields


def get_visible_custom_fields():
    return frappe.db.get_all(
        "HD Ticket Template Field",
        {"parent": "Default", "hide_from_customer": 0},
        pluck="fieldname",
    )


def default_view_exists(doctype):
    return frappe.db.exists(
        "HD View",
        {
            "is_default": 1,
            "user": frappe.session.user,
            "dt": doctype,
        },
    )


def handle_default_view(doctype, _list, show_customer_portal_fields):
    [columns, rows] = frappe.get_value(
        "HD View",
        {
            "is_default": 1,
            "user": frappe.session.user,
            "dt": doctype,
        },
        ["columns", "rows"],
    )
    columns = frappe.parse_json(columns)
    rows = frappe.parse_json(rows)

    if not columns:
        columns = (
            _list.default_list_data(show_customer_portal_fields).get("columns")
            if doctype == "HD Ticket"
            else _list.default_list_data().get("columns")
        )
    if not rows:
        rows = _list.default_list_data().get("rows")

    return [columns, rows]


def handle_at_me_support(filters):
    # Converts @me in filters to current user
    for key in filters:
        value = filters[key]
        if isinstance(value, list):
            if "@me" in value:
                value[value.index("@me")] = frappe.session.user
            elif "%@me%" in value:
                index = [i for i, v in enumerate(value) if v == "%@me%"]
                for i in index:
                    value[i] = "%" + frappe.session.user + "%"
        elif value == "@me":
            filters[key] = frappe.session.user

    return filters


# filters out tickets based on team restrictions
def handle_team_restrictions(filters):
    enable_restrictions = frappe.db.get_single_value(
        "HD Settings", "restrict_tickets_by_agent_group"
    )
    if not enable_restrictions:
        return
    show_tickets_without_team = frappe.db.get_single_value(
        "HD Settings", "do_not_restrict_tickets_without_an_agent_group"
    )

    QBTeam = frappe.qb.DocType("HD Team")
    QBTeamMember = frappe.qb.DocType("HD Team Member")

    teams = (
        frappe.qb.from_(QBTeamMember)
        .where(QBTeamMember.user == frappe.session.user)
        .join(QBTeam)
        .on(QBTeam.name == QBTeamMember.parent)
        .select(QBTeam.team_name, QBTeam.ignore_restrictions)
        .run(as_dict=True)
    )

    if any([team.get("ignore_restrictions") for team in teams]):
        return

    team_names = [t.get("team_name") for t in teams]

    if show_tickets_without_team:
        team_names = team_names + [""]

    if not filters:
        filters.append({"agent_group": ["in", team_names]})
    else:
        filters["agent_group"] = ["in", team_names]
