interface DocType {
  name: string;
  creation: string;
  modified: string;
  owner: string;
  modified_by: string;
}

interface ChildDocType extends DocType {
  parent?: string;
  parentfield?: string;
  parenttype?: string;
  idx?: number;
}

// Last updated: 2025-08-18 19:52:52.191504
export interface HDTicketStatus extends DocType {
  /** Color: Select */
  color?:
    | "Black"
    | "Gray"
    | "Blue"
    | "Green"
    | "Red"
    | "Pink"
    | "Orange"
    | "Amber"
    | "Yellow"
    | "Cyan"
    | "Teal"
    | "Violet"
    | "Purple";
  /** Label: Data */
  label_agent: string;
  /** Show end users a different view: Check */
  different_view: 0 | 1;
  /** Label (customer view): Data */
  label_customer?: string;
  /** Category: Select */
  category: "Open" | "Paused" | "Resolved";
  /** Order: Int */
  order?: number;
  /** Enabled: Check */
  enabled: 0 | 1;
  /** Default status: Check */
  default_status?: 0 | 1;
  parsed_color?: string;
}
