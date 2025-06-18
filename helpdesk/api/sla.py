import frappe
import ast
import json
from frappe.utils import cint, getdate
from frappe import _


@frappe.whitelist()
def duplicate_sla(docname):
    doc = frappe.get_doc("HD Service Level Agreement", docname)
    doc.name = ""
    doc.service_level = f"{doc.service_level} (Duplicate)"
    doc.insert()
    return "success"


@frappe.whitelist()
def duplicate_priority(docname):
    doc = frappe.get_doc("HD Service Level Priority", docname)
    doc.name = ""
    doc.default_priority = 0
    doc.insert()
    return "success"


@frappe.whitelist()
def get_sla(docname):
    sla = frappe.get_doc("HD Service Level Agreement", docname)
    if sla.condition:
        sla.condition = json.dumps(convert_to_object(sla.condition))
    return sla


@frappe.whitelist()
def save_sla(doc, is_new):
    # based on doc.support_and_resolution generate weekend holidays list
    # remove holidays from service holiday list based on days which are in doc.support_and_resolution
    # remove objects from doc.support_and_resolution which have key is_holiday and value is true
    #

    holiday_list = frappe.get_doc("HD Service Holiday List", doc["holiday_list"])

    weekend_holidays = []
    weekends = list(
        filter(lambda x: x.get("is_holiday"), doc["support_and_resolution"])
    )
    for weekend in weekends:
        days = get_weekly_off_dates(
            doc["start_date"],
            doc["end_date"],
            weekend["workday"],
            holiday_list.holidays,
        )
        weekend_holidays.extend(days)

    # Get holidays without weekends
    old_holiday_list = [
        h
        for h in holiday_list.holidays
        if not h.get("weekly_off") or cint(h.get("weekly_off")) == 0
    ]
    new_workdays_list = [
        h for h in doc["support_and_resolution"] if not h.get("is_holiday")
    ]

    if is_new:
        frappe.client.insert(
            {
                **doc,
                "doctype": "HD Service Level Agreement",
                "support_and_resolution": new_workdays_list,
                "condition": convert_to_conditions(doc["condition"]),
            }
        )
        holiday_list.update(
            {
                "from_date": doc["start_date"],
                "to_date": doc["end_date"],
                "holidays": old_holiday_list + weekend_holidays,
            }
        )
        holiday_list.save()
    else:
        sla = frappe.get_doc("HD Service Level Agreement", doc["name"])
        sla.update(
            {
                **doc,
                "support_and_resolution": new_workdays_list,
                "condition": convert_to_conditions(doc["condition"]),
            }
        )
        print("@@@@@@@@@@@@@@", doc["condition"])
        print("@@@@@@@@@@@@@@", convert_to_conditions(doc["condition"]))
        sla.save()
        holiday_list.update(
            {
                "from_date": doc["start_date"],
                "to_date": doc["end_date"],
                "holidays": old_holiday_list + weekend_holidays,
            }
        )
        holiday_list.save()
    return "success", new_workdays_list, weekend_holidays


def get_weekly_off_dates(start_date, end_date, weekly_off, holidays):
    date_list = get_weekly_off_date_list(start_date, end_date, weekly_off, holidays)
    holidays = []
    for i, d in enumerate(date_list):
        ch = {
            "description": _(weekly_off),
            "holiday_date": d,
            "weekly_off": 1,
            "idx": i + 1,
        }
        holidays.append(ch)
    return holidays


def get_weekly_off_date_list(start_date, end_date, weekly_off, holidays):
    start_date, end_date = getdate(start_date), getdate(end_date)

    import calendar
    from datetime import timedelta

    from dateutil import relativedelta

    date_list = []
    existing_date_list = []
    weekday = getattr(calendar, (weekly_off).upper())
    reference_date = start_date + relativedelta.relativedelta(weekday=weekday)

    existing_date_list = [getdate(holiday.holiday_date) for holiday in holidays]

    while reference_date <= end_date:
        if reference_date not in existing_date_list:
            date_list.append(reference_date)
        reference_date += timedelta(days=7)

    return date_list


def convert_to_conditions(conditions, is_nested=False):
    """
    Convert conditions array to Python string

    Args:
        conditions (list/dict): List of conditions or a single condition dict
        is_nested (bool): Whether this is a nested condition (for internal use)

    Returns:
        str: Python condition string
    """
    if not conditions:
        return ""

    if isinstance(conditions, dict):
        conditions = [conditions]

    conditions_str = []

    for condition in conditions:
        field = condition.get("field")
        operator = condition.get("operator", "==").lower()
        value = condition.get("value")
        conjunction = condition.get("conjunction", "and").lower()

        # Handle nested conditions
        if field == "group" and isinstance(value, list):
            nested_condition = convert_to_conditions(value, is_nested=True)
            conditions_str.append(f"({nested_condition})")
            continue

        # Skip if field is not properly defined
        if not isinstance(field, dict) or "fieldname" not in field:
            continue

        fieldname = field["fieldname"]
        fieldtype = field.get("fieldtype", "")

        # Format field access
        field_access = f"doc.{fieldname}"

        # Format operator
        operator_map = {
            # Basic comparisons
            "equals": "==",
            "=": "==",
            "!=": "!=",
            "not equals": "!=",
            "<": "<",
            "<=": "<=",
            ">": ">",
            ">=": ">=",
            # Membership
            "in": "in",
            "not in": "not in",
            # String matching
            "like": "like",
            "not like": "not like",
            # Identity
            "is": "is",
            "is not": "is not",
            # Date specific
            "between": "between",
            "timespan": "timespan",
        }

        op = operator_map.get(operator, operator)

        # Format value
        if isinstance(value, str):
            # Handle special cases for _assign field
            if fieldname == "_assign":
                if op == "like":
                    op = "like"
                    value_str = f"'%{value}%'"
                elif op == "not like":
                    op = "not like"
                    value_str = f"'%{value}%'"
                elif op == "is":
                    value_str = "None"
            # Handle Check/Boolean fields
            elif fieldtype == "Check":
                if value.lower() in ("yes", "true", "1"):
                    value_str = "1"
                else:
                    value_str = "0"
                # Special case for boolean fields
                if op == "==" and value_str == "1":
                    conditions_str.append(field_access)
                    continue
                elif op == "==" and value_str == "0":
                    conditions_str.append(f"not {field_access}")
                    continue
            # Handle date timespan
            elif op == "timespan":
                # This would need to be expanded based on actual timespan handling
                conditions_str.append(f"# Timespan: {value} not implemented")
                continue
            # Handle between operator (typically for dates)
            elif op == "between" and "," in value:
                start, end = [v.strip() for v in value.split(",")]
                conditions_str.append(
                    f"({field_access} >= '{start}' and {field_access} <= '{end}')"
                )
                continue
            # Handle string values with in/not in operators
            elif op in ("in", "not in") and "," in value:
                # Handle comma-separated values
                items = [f"'{v.strip()}'" for v in value.split(",")]
                value_str = f"[{', '.join(items)}]"
            # Handle LIKE/NOT LIKE with wildcards
            elif op in ("like", "not like"):
                value_str = f"'%{value}%'"
            else:
                value_str = f"'{value}'"
        # Handle numeric values
        elif isinstance(value, (int, float, bool)):
            value_str = str(value).lower() if isinstance(value, bool) else str(value)
        # Handle None/Null values
        elif value is None:
            value_str = "None"
        # Handle other types (lists, dicts, etc.)
        else:
            value_str = str(value)

        # Build the condition string
        condition_str = f"{field_access} {op} {value_str}"

        # Special case for Check fields
        if fieldtype == "Check" and op == "==" and value_str in ("0", "1"):
            if value_str == "1":
                condition_str = field_access
            else:
                condition_str = f"not {field_access}"

        conditions_str.append(condition_str)

    # Join conditions with conjunctions
    if not conditions_str:
        return ""

    result = f" {conjunction} ".join(conditions_str)

    # Remove unnecessary parentheses for non-nested single conditions
    if (
        not is_nested
        and len(conditions) == 1
        and not any(c in result for c in ["(", ")"])
    ):
        return result

    # Ensure proper spacing around operators for better readability
    result = result.replace("  ", " ").replace("  ", " ").strip()

    # Only add parentheses for nested conditions with multiple conditions
    if is_nested and len(conditions) > 1:
        result = f"({result})"

    # Remove any double parentheses that might have been added
    while "((" in result and "))" in result:
        result = result.replace("((", "(").replace("))", ")")

    return result


def convert_to_object(condition_str):
    if not condition_str:
        return []

    fields_meta = {f.fieldname: f for f in frappe.get_meta("HD Ticket").fields}

    def get_field_info(fieldname):
        meta = fields_meta.get(fieldname)
        if not meta:
            return {
                "value": fieldname,
                "fieldname": fieldname,
                "fieldtype": "Data",
                "label": fieldname.replace("_", " ").title(),
            }
        return {
            "value": fieldname,
            "fieldname": meta.fieldname,
            "fieldtype": meta.fieldtype,
            "label": meta.label,
            "options": meta.options,
        }

    def get_operator_str(op):
        return {
            ast.Eq: "equals",
            ast.NotEq: "not equals",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
            ast.In: "in",
            ast.NotIn: "not in",
        }.get(type(op), "")

    def parse_node(node, is_top_level=False):
        if isinstance(node, ast.BoolOp):
            conjunction = "and" if isinstance(node.op, ast.And) else "or"

            child_results = [parse_node(v) for v in node.values]

            for i in range(1, len(child_results)):
                child = child_results[i]
                if child and child[0]:
                    child[0]["conjunction"] = conjunction

            flat_conditions = []
            for child in child_results:
                if child:
                    flat_conditions.extend(child)

            if len(node.values) > 1 and not is_top_level:
                return [
                    {
                        "field": "group",
                        "operator": "equals",
                        "value": flat_conditions,
                    }
                ]

            return flat_conditions

        elif isinstance(node, ast.Compare):
            fieldname = node.left.attr
            op = get_operator_str(node.ops[0])
            val = ast.literal_eval(node.comparators[0])

            if fields_meta.get(fieldname, {}).get("fieldtype") == "Check":
                value = "Yes" if val else "No"
            elif isinstance(val, list):
                value = ", ".join(map(str, val))
            else:
                value = str(val)

            return [
                {
                    "field": get_field_info(fieldname),
                    "operator": op,
                    "value": value,
                }
            ]

        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            condition = parse_node(node.operand)
            if condition and condition[0]:
                condition[0]["value"] = "No"
                return condition
            return None

        elif isinstance(node, ast.Attribute):
            fieldname = node.attr
            if fields_meta.get(fieldname, {}).get("fieldtype") == "Check":
                return [
                    {
                        "field": get_field_info(fieldname),
                        "operator": "equals",
                        "value": "Yes",
                    }
                ]
            return None

        elif isinstance(node, ast.Expr):
            return parse_node(node.value, is_top_level)

        return None

    try:
        parsed_ast = ast.parse(condition_str.strip(), mode="eval")
        conditions = parse_node(parsed_ast.body, is_top_level=True)
        return conditions or []

    except (SyntaxError, ValueError) as e:
        frappe.log_error(f"Error parsing condition string: {e}", "SLA API Error")
        return []
