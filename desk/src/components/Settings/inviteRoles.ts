import { __ } from "@/translation";

export type Role = "Agent" | "Agent Manager" | "System Manager";
export type RoleOption = {
  label: string;
  value: Role;
  description: string;
};

export const roleToLabel = (role: Role) => {
  switch (role) {
    case "Agent":
      return "Agent";
    case "Agent Manager":
      return "Manager";
    case "System Manager":
      return "Admin";
    default:
      const x: never = role;
      throw new Error(`Invalid role: ${x}`);
  }
};

/** The roles `user` may grant when inviting; Agent is always first. */
export function getInviteRoleOptions(user: {
  isAdmin: boolean;
  isManager: boolean;
}): [RoleOption, ...RoleOption[]] {
  const roleOptions: [RoleOption, ...RoleOption[]] = [
    {
      label: roleToLabel("Agent"),
      value: "Agent",
      description: __(
        "Can work on tickets, create custom views and manage private views."
      ),
    },
  ];
  const managerRoleOption: RoleOption = {
    label: roleToLabel("Agent Manager"),
    value: "Agent Manager",
    description: __(
      "Can invite new agents, manage tickets, create custom views and manage public views."
    ),
  };
  if (user.isAdmin) {
    roleOptions.push(managerRoleOption, {
      label: roleToLabel("System Manager"),
      value: "System Manager",
      description: __("Can manage all aspects of Helpdesk."),
    });
  } else if (user.isManager) {
    roleOptions.push(managerRoleOption);
  }
  return roleOptions;
}

/** The roles an invitation for `selectedRole` carries: it includes the lower ones. */
export const getInviteByEmailRoles = (selectedRole: Role) => {
  const res: Role[] = [];
  switch (selectedRole) {
    case "System Manager":
      res.push("Agent", "Agent Manager");
      break;
    case "Agent Manager":
      res.push("Agent");
      break;
    case "Agent":
      break;
    default:
      const x: never = selectedRole;
      throw new Error(`Invalid selected role: ${x}`);
  }
  res.push(selectedRole);
  return res;
};
