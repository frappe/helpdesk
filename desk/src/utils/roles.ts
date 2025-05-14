import { getUserRole } from "./auth";

export interface Role {
  label: string;
  value: string;
  selected: boolean;
  onClick: () => void;
}

/**
 * Gets available roles for a user based on their current role
 * - Agent users can only see Agent role
 * - Agent Manager users can see Agent Manager and Agent roles
 * - Administrator users can see all three roles
 * - The roles are ordered: Administrator, Agent Manager, Agent
 *
 * @param user - Username to get roles for
 * @returns Array of role objects with label, value, selected status and click handler
 */
export function getRoles(user: string): Role[] {
  const userRole = getUserRole(user);

  // Default role available to all
  const roles: Role[] = [
    {
      label: "Agent",
      value: "Agent",
      selected: userRole === "Agent",
      onClick: () => console.log("Agent selected for", user),
    },
  ];

  // Add Agent Manager role if user is Agent Manager or Administrator
  if (userRole === "Agent Manager" || userRole === "Administrator") {
    roles.unshift({
      label: "Agent Manager",
      value: "Agent Manager",
      selected: userRole === "Agent Manager",
      onClick: () => console.log("Agent Manager selected for", user),
    });
  }

  // Add Administrator role if user is Administrator
  if (userRole === "Administrator") {
    roles.unshift({
      label: "Administrator",
      value: "Administrator",
      selected: userRole === "Administrator",
      onClick: () => console.log("Administrator selected for", user),
    });
  }

  return roles;
}

/**
 * Updates a user's role in the system
 *
 * @param user - Username to update role for
 * @param role - New role to assign
 * @returns Promise that resolves when role is updated
 */
export async function updateUserRole(
  user: string,
  role: string
): Promise<void> {
  // Implementation would call an API endpoint to update the user's role
  // This is a placeholder for the actual implementation
  console.log(`Updating user ${user} to role ${role}`);

  // Example implementation might look like:
  // return await call('helpdesk.api.agent.update_role', {
  //   user,
  //   role
  // });
}
