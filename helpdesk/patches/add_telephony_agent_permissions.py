from helpdesk.setup.install import (
    add_agent_manager_permissions,
    update_agent_role_permissions,
)


def execute():
    update_agent_role_permissions()
    add_agent_manager_permissions()
