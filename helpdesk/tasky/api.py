"""Tasky API — checklist-driven project management on ERPNext Project/Task."""

import json

import frappe
from frappe import _


def _resolve_project(project):
    """Find project by name or project_name."""
    if frappe.db.exists("Project", project):
        return project
    name = frappe.db.get_value("Project", {"project_name": project}, "name")
    if name:
        return name
    frappe.throw(_("Project not found: {0}").format(project))


def _format_task(task):
    """Normalize a Task dict for frontend consumption."""
    assign_raw = task.pop("_assign", None) or ""
    try:
        assigned = json.loads(assign_raw)
    except (json.JSONDecodeError, TypeError):
        assigned = []
    return {
        **task,
        "category": task.get("custom_category") or "",
        "phase": task.get("custom_phase") or "",
        "module": task.get("custom_module") or "",
        "estimated_hours": task.get("custom_estimated_hours") or 0,
        "actual_hours": task.get("custom_actual_hours") or 0,
        "start_date": task.get("exp_start_date"),
        "due_date": task.get("exp_end_date"),
        "assigned_to": assigned[0] if assigned else None,
        "assignees": assigned,
        "custom_timer_start": task.get("custom_timer_start"),
        "custom_timer_elapsed": task.get("custom_timer_elapsed") or 0,
    }


@frappe.whitelist()
def complete_task(task, hours_worked=0, notes=""):
    """Complete a task with optional timesheet entry."""
    doc = frappe.get_doc("Task", str(task))
    doc.status = "Completed"
    doc.custom_actual_hours = (doc.custom_actual_hours or 0) + (float(hours_worked) or 0)
    doc.custom_timer_start = None
    doc.custom_timer_elapsed = 0
    doc.save()

    if float(hours_worked) > 0:
        try:
            employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
            ts = frappe.get_doc({
                "doctype": "Timesheet",
                "title": f"Task: {doc.subject}",
                "employee": employee,
                "time_logs": [{
                    "task": doc.name,
                    "from_time": frappe.utils.now(),
                    "hours": float(hours_worked),
                    "description": notes or f"Completed task: {doc.subject}",
                    "project": doc.project,
                    "completed": 1,
                }],
            })
            ts.flags.ignore_permissions = True
            ts.flags.ignore_mandatory = True
            ts.insert(ignore_permissions=True)
            try:
                ts.submit()
            except Exception:
                pass
            frappe.db.commit()
        except Exception:
            frappe.log_error(title="complete_task Timesheet Error")

    frappe.db.commit()
    return _format_task(doc.as_dict())


def _compute_due_date(project_start, phase_order, task_sort_order):
    """Compute start and end dates based on project start + phase delay + task stagger."""
    if not project_start:
        return None, None
    from datetime import timedelta
    base = project_start
    if isinstance(base, str):
        base = frappe.utils.get_datetime(base)
    phase_days = phase_order * 7
    start = base + timedelta(days=phase_days + (task_sort_order or 0))
    end = start + timedelta(days=3)
    if hasattr(start, "date"):
        start = start.date()
    if hasattr(end, "date"):
        end = end.date()
    return start, end


@frappe.whitelist()
def create_project(project_name, expected_start_date=None, expected_end_date=None, members="[]"):
    """Create a new ERPNext Project with optional team members."""
    import json
    existing = frappe.db.get_value("Project", {"project_name": project_name}, "name")
    if existing:
        frappe.throw(_("Project with this name already exists: {0}").format(existing))

    members_list = json.loads(str(members)) if isinstance(members, str) else (members or [])

    doc = frappe.get_doc({
        "doctype": "Project",
        "project_name": project_name,
        "expected_start_date": expected_start_date or None,
        "expected_end_date": expected_end_date or None,
        "status": "Open",
    })
    for m in members_list:
        doc.append("users", {
            "user": m.get("user", ""),
            "custom_role": m.get("custom_role", ""),
        })
    doc.insert()
    frappe.db.commit()
    return {"name": doc.name, "project_name": doc.project_name, "status": doc.status}


@frappe.whitelist()
def generate_checklist(project, template):
    """Clone template tasks into ERPNext Project + Tasks."""
    project = _resolve_project(str(project))
    template_name = str(template)

    if not frappe.db.exists("Project", project):
        frappe.throw(_("Project not found"))
    if not frappe.db.exists("HD Task Template", template_name):
        frappe.throw(_("Template not found"))

    CATEGORY_TO_ROLE = {
        "Functional": "Functional Consultant",
        "Development": "Developer",
        "Support": "Support Engineer",
    }

    template_doc = frappe.get_doc("HD Task Template", template_name)

    project_users = frappe.get_all("Project User", {"parent": project}, ["user", "custom_role"])
    project_start = frappe.db.get_value("Project", project, "expected_start_date")

    # Collect distinct phase names in order
    phases_seen = []
    for ttask in template_doc.tasks:
        if ttask.phase_name and ttask.phase_name not in phases_seen:
            phases_seen.append(ttask.phase_name)

    role_pool = {}
    for u in project_users:
        role = u.get("custom_role") or "Common"
        if role not in role_pool:
            role_pool[role] = []
        role_pool[role].append(u["user"])

    role_counter = {}
    all_users = [u["user"] for u in project_users]

    def pick_user(category):
        role = CATEGORY_TO_ROLE.get(category, "Common")
        pool = role_pool.get(role, [])
        if pool:
            idx = role_counter.get(role, 0) % len(pool)
            user = pool[idx]
            role_counter[role] = idx + 1
            return user
        if all_users:
            idx = role_counter.get("__all__", 0) % len(all_users)
            user = all_users[idx]
            role_counter["__all__"] = idx + 1
            return user
        return None

    created_count = 0
    for ttask in template_doc.tasks:
        task_start, task_end = _compute_due_date(
            project_start,
            phases_seen.index(ttask.phase_name) if ttask.phase_name in phases_seen else 0,
            ttask.sort_order,
        )

        task_doc = frappe.get_doc({
            "doctype": "Task",
            "subject": ttask.task_name,
            "project": project,
            "description": ttask.description or "",
            "custom_category": ttask.category,
            "custom_phase": ttask.phase_name or "",
            "custom_module": ttask.module_name or "",
            "custom_estimated_hours": ttask.estimated_hours or 0,
            "priority": ttask.default_priority or "Medium",
            "status": "Open",
            "exp_start_date": task_start,
            "exp_end_date": task_end,
        })
        assigned = pick_user(ttask.category)
        if assigned:
            _assign_user(task_doc, assigned)
        task_doc.insert()
        created_count += 1

    frappe.db.commit()
    return {"tasks_created": created_count}


def _assign_user(task_doc, user):
    """Set _assign field on a Task document to assign it to a user."""
    if not user:
        return
    user = str(user).strip()
    if frappe.db.exists("User", user):
        import json
        task_doc._assign = json.dumps([user])


@frappe.whitelist()
def add_task(project, task_name, phase="", category="Functional", priority="Medium", estimated_hours=0, assigned_to="", due_date=None):
    """Add a single task to a project's checklist."""
    project = _resolve_project(str(project))
    doc = frappe.get_doc({
        "doctype": "Task",
        "subject": str(task_name),
        "project": project,
        "custom_category": str(category),
        "custom_phase": str(phase) if phase else "",
        "custom_estimated_hours": float(estimated_hours) or 0,
        "priority": str(priority),
        "status": "Open",
        "exp_end_date": due_date if due_date and due_date != "null" else None,
    })
    _assign_user(doc, assigned_to)
    doc.insert()
    frappe.db.commit()
    return _format_task(doc.as_dict())


@frappe.whitelist()
@frappe.whitelist()
def get_my_tasks(project=None, status=None, limit=50):
    """Get tasks assigned to current user."""
    user = frappe.session.user

    filters = {"_assign": ("like", f"%{user}%")}
    if project:
        filters["project"] = _resolve_project(str(project)) if not frappe.db.exists("Project", project) else str(project)
    if status:
        filters["status"] = str(status)

    tasks = frappe.get_all(
        "Task",
        filters=filters,
        fields=["name", "subject", "project", "custom_category", "custom_phase",
                "status", "priority", "exp_end_date", "custom_estimated_hours", "_assign"],
        order_by="custom_phase asc",
        limit=limit,
    )
    return [_format_task(t) for t in tasks]


@frappe.whitelist()
def get_task_detail(task):
    """Get a single task with all fields."""
    task = str(task)
    doc = frappe.get_doc("Task", task)
    return _format_task(doc.as_dict())


@frappe.whitelist()
def update_task_status(task, status):
    """Update a task's status."""
    frappe.db.set_value("Task", str(task), "status", str(status))
    frappe.db.commit()
    return {"status": str(status)}


@frappe.whitelist()
def get_project_dashboard(project):
    """Get aggregate stats and phase data for the PM dashboard."""
    project = _resolve_project(str(project))

    total_tasks = frappe.db.count("Task", {"project": project})
    completed = frappe.db.count("Task", {"project": project, "status": "Completed"})
    in_progress = frappe.db.count("Task", {"project": project, "status": "Working"})
    pending = frappe.db.count("Task", {"project": project, "status": "Open"})
    reviewing = frappe.db.count("Task", {"project": project, "status": "Pending Review"})
    cancelled = frappe.db.count("Task", {"project": project, "status": "Cancelled"})
    overdue = frappe.db.count("Task", {
        "project": project,
        "exp_end_date": ("<", frappe.utils.today()),
        "status": ("not in", ["Completed", "Cancelled"]),
    })
    progress_pct = round((completed / total_tasks * 100), 1) if total_tasks > 0 else 0

    phase_rows = frappe.db.sql("""
        SELECT custom_phase, COUNT(*) as total_count,
               SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_count
        FROM `tabTask`
        WHERE project = %s AND custom_phase IS NOT NULL AND custom_phase != ''
        GROUP BY custom_phase
        ORDER BY MIN(creation) ASC
    """, project, as_dict=True)

    phases = []
    for row in phase_rows:
        pc = row["total_count"]
        cc = row["completed_count"] or 0
        phases.append({
            "name": row["custom_phase"],
            "phase_name": row["custom_phase"],
            "total_count": pc,
            "completed_count": cc,
            "progress_pct": round((cc / pc * 100), 1) if pc > 0 else 0,
        })

    tasks = frappe.get_all("Task",
        filters={"project": project},
        fields=["name", "subject", "custom_category", "custom_phase", "status",
                "priority", "exp_end_date", "custom_estimated_hours", "_assign"],
        order_by="custom_phase asc, subject asc")

    formatted_tasks = [_format_task(t) for t in tasks]

    return {
        "phases": phases,
        "tasks": formatted_tasks,
        "stats": {
            "total": total_tasks,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "reviewing": reviewing,
            "cancelled": cancelled,
            "blocked": cancelled,
            "overdue": overdue,
            "completion_pct": progress_pct,
        },
    }


@frappe.whitelist()
def get_phase_tasks(project, phase):
    """Get all tasks in a phase for the given project."""
    project = _resolve_project(str(project))
    phase = str(phase)
    tasks = frappe.get_all("Task",
        filters={"project": project, "custom_phase": phase},
        fields=["name", "subject", "custom_category", "custom_phase", "status",
                "priority", "exp_end_date", "custom_estimated_hours", "_assign"],
        order_by="subject asc")
    return [_format_task(t) for t in tasks]


@frappe.whitelist()
def get_kanban_tasks(project):
    """Get tasks grouped by status for kanban board."""
    project = _resolve_project(str(project))
    tasks = frappe.get_all("Task",
        filters={"project": project},
        fields=["name", "subject", "custom_category", "custom_phase", "status",
                "priority", "exp_end_date", "custom_estimated_hours", "_assign",
                "custom_timer_start", "custom_timer_elapsed"],
        order_by="custom_phase asc, subject asc")

    columns = {
        "Open": [],
        "Working": [],
        "Pending Review": [],
        "Completed": [],
        "Cancelled": [],
    }
    for t in tasks:
        status = t.get("status") or "Open"
        if status not in columns:
            status = "Open"
        columns[status].append(_format_task(t))

    return {"columns": columns}


@frappe.whitelist()
def get_templates():
    """List all available implementation templates."""
    return frappe.get_all("HD Task Template",
        fields=["name", "template_name", "industry", "description"])


@frappe.whitelist()
def create_template(template_name, industry="", description="", tasks="[]"):
    """Create a new HD Task Template with tasks."""
    import json
    tasks_list = json.loads(str(tasks)) if isinstance(tasks, str) else tasks

    existing = frappe.db.exists("HD Task Template", {"template_name": template_name})
    if existing:
        frappe.throw(_("Template '{0}' already exists").format(template_name))

    doc = frappe.get_doc({
        "doctype": "HD Task Template",
        "template_name": template_name,
        "industry": industry,
        "description": description,
        "tasks": [],
    })
    for t in tasks_list:
        doc.append("tasks", {
            "task_name": t.get("task_name", ""),
            "phase_name": t.get("phase_name", ""),
            "category": t.get("category", "Functional"),
            "default_priority": t.get("default_priority", "Medium"),
            "estimated_hours": t.get("estimated_hours", 0),
        })
    doc.insert()
    frappe.db.commit()
    return {"name": doc.name, "template_name": doc.template_name}


@frappe.whitelist()
def get_template(template):
    """Get a single template with all tasks."""
    doc = frappe.get_doc("HD Task Template", str(template))
    return {
        "name": doc.name,
        "template_name": doc.template_name,
        "industry": doc.industry or "",
        "description": doc.description or "",
        "tasks": [{"task_name": t.task_name, "phase_name": t.phase_name or "", "category": t.category,
                    "default_priority": t.default_priority, "estimated_hours": t.estimated_hours, "sort_order": t.sort_order}
                  for t in doc.tasks],
    }


@frappe.whitelist()
def update_template(template, template_name, industry="", description="", tasks="[]"):
    """Update an existing HD Task Template."""
    import json
    tasks_list = json.loads(str(tasks)) if isinstance(tasks, str) else tasks
    doc = frappe.get_doc("HD Task Template", str(template))
    doc.template_name = template_name
    doc.industry = industry
    doc.description = description
    doc.tasks = []
    for t in tasks_list:
        doc.append("tasks", {
            "task_name": t.get("task_name", ""),
            "phase_name": t.get("phase_name", ""),
            "category": t.get("category", "Functional"),
            "default_priority": t.get("default_priority", "Medium"),
            "estimated_hours": t.get("estimated_hours", 0),
        })
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"name": doc.name, "template_name": doc.template_name}


@frappe.whitelist()
def get_project_detail(project):
    """Get ERPNext project details."""
    project = _resolve_project(str(project))
    doc = frappe.get_doc("Project", project)
    return {
        "name": doc.name,
        "project_name": doc.project_name,
        "status": doc.status,
        "expected_start_date": str(doc.expected_start_date) if doc.expected_start_date else None,
        "expected_end_date": str(doc.expected_end_date) if doc.expected_end_date else None,
        "users": [{"user": u.user, "full_name": u.full_name} for u in doc.users] if doc.users else [],
    }


@frappe.whitelist()
def get_users():
    """List enabled users for assignment dropdowns."""
    return frappe.get_all("User", {"enabled": 1}, ["name", "full_name", "email", "user_image"], order_by="full_name asc")


@frappe.whitelist()
def get_projects():
    """List all ERPNext Projects."""
    return frappe.get_all("Project",
        fields=["name", "project_name", "status", "expected_start_date", "expected_end_date", "priority"])


# === Timer ===

@frappe.whitelist()
def start_timer(task):
    """Start the timer on a task."""
    frappe.db.set_value("Task", str(task), "custom_timer_start", frappe.utils.now())
    frappe.db.commit()
    return {"ok": 1}


@frappe.whitelist()
def stop_timer(task):
    """Stop the timer and persist elapsed."""
    task_id = str(task)
    timer_start = frappe.db.get_value("Task", task_id, "custom_timer_start")
    if not timer_start:
        return {"elapsed": 0}
    from datetime import datetime
    start = timer_start
    if isinstance(start, str):
        start = datetime.fromisoformat(start)
    elapsed = (datetime.now() - start).total_seconds() / 3600.0
    actual = frappe.db.get_value("Task", task_id, "custom_actual_hours") or 0
    paused = frappe.db.get_value("Task", task_id, "custom_timer_elapsed") or 0
    frappe.db.set_value("Task", task_id, "custom_timer_start", None)
    frappe.db.set_value("Task", task_id, "custom_actual_hours", actual + round(elapsed, 2))
    frappe.db.set_value("Task", task_id, "custom_timer_elapsed", paused + round(elapsed, 2))
    frappe.db.commit()
    return {"elapsed": round(elapsed, 2)}


@frappe.whitelist()
def move_task(task, new_status):
    """Move a task column — update timer, status, elapsed. No doc.save() to prevent deadlock."""
    task_id = str(task)
    old_status = frappe.db.get_value("Task", task_id, "status")
    elapsed_paused = frappe.db.get_value("Task", task_id, "custom_timer_elapsed") or 0
    timer_start = frappe.db.get_value("Task", task_id, "custom_timer_start")
    actual = frappe.db.get_value("Task", task_id, "custom_actual_hours") or 0
    elapsed_this_move = 0

    if old_status == new_status:
        return {"status": old_status, "elapsed": 0}

    # Leaving Working: accumulate elapsed from running timer
    if old_status == "Working" and timer_start:
        from datetime import datetime
        start = timer_start
        if isinstance(start, str):
            start = datetime.fromisoformat(start)
        elapsed_this_move = (datetime.now() - start).total_seconds() / 3600.0
        frappe.db.set_value("Task", task_id, "custom_timer_start", None)
        frappe.db.set_value("Task", task_id, "custom_actual_hours", actual + round(elapsed_this_move, 2))

        # Pausing to Open or PendingReview: save elapsed so timer resumes
        if new_status in ("Open", "Pending Review"):
            frappe.db.set_value("Task", task_id, "custom_timer_elapsed", (elapsed_paused or 0) + round(elapsed_this_move, 2))

    # Entering Working: start timer (fresh or resume)
    if new_status == "Working":
        frappe.db.set_value("Task", task_id, "custom_timer_start", frappe.utils.now())

    frappe.db.set_value("Task", task_id, "status", new_status)
    frappe.db.commit()
    return {"status": new_status, "elapsed": round(elapsed_this_move, 2)}


@frappe.whitelist()
def get_timer(task):
    """Get current timer state for a task."""
    doc = frappe.get_doc("Task", str(task))
    if not doc.custom_timer_start:
        return {"running": False, "elapsed": 0, "timer_start": None}
    from datetime import datetime
    start = doc.custom_timer_start
    if isinstance(start, str):
        start = datetime.fromisoformat(start)
    elapsed = (datetime.now() - start).total_seconds() / 3600.0
    return {"running": True, "elapsed": round(elapsed, 2), "timer_start": str(start)}


@frappe.whitelist()
def get_my_timesheets(limit=20):
    """List my timesheets with project info."""
    timesheets = frappe.get_all("Timesheet",
        filters={"owner": frappe.session.user},
        fields=["name", "title", "status", "total_hours", "creation", "modified"],
        order_by="modified desc",
        limit=limit)
    for ts in timesheets:
        projects = frappe.db.sql("""
            SELECT DISTINCT td.project
            FROM `tabTimesheet Detail` td
            WHERE td.parent = %s AND td.project IS NOT NULL AND td.project != ''
            LIMIT 3
        """, ts["name"], as_dict=True)
        ts["projects"] = [p["project"] for p in projects]
        if ts["projects"]:
            proj_name = frappe.db.get_value("Project", ts["projects"][0], "project_name")
            ts["project_name"] = proj_name
    return timesheets


@frappe.whitelist()
def get_project_tasks(project):
    """Get all active tasks in a project for dropdown."""
    project = _resolve_project(str(project))
    return frappe.get_all("Task",
        filters={"project": project, "status": ("not in", ["Completed", "Cancelled"])},
        fields=["name", "subject"],
        order_by="subject asc")


@frappe.whitelist()
def create_timesheet(title, project=None, task=None, hours=0, notes=""):
    """Manually create a timesheet."""
    employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    from_time = frappe.utils.now()
    ts = frappe.get_doc({
        "doctype": "Timesheet",
        "title": title,
        "employee": employee,
        "time_logs": [{
            "task": task,
            "project": project,
            "from_time": from_time,
            "hours": float(hours) or 0,
            "description": notes,
        }],
    })
    ts.flags.ignore_permissions = True
    ts.flags.ignore_mandatory = True
    ts.insert(ignore_permissions=True)
    try:
        ts.submit()
    except Exception:
        pass
    frappe.db.commit()
    return {"name": ts.name, "title": title, "total_hours": float(hours), "status": ts.status}
