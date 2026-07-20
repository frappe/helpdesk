export interface Option {
  label: string;
  value: string;
}

// A dropdown rendered beneath a text question (e.g. org name + company size).
export interface DropdownConfig {
  key: string;
  label: string;
  placeholder: string;
  options: Option[];
}

export interface TextQuestion {
  key: string;
  title: string;
  type: "text";
  label?: string;
  placeholder?: string;
  multiline?: boolean;
  required?: boolean;
  dropdown?: DropdownConfig;
}

export interface ChoiceQuestion {
  key: string;
  title: string;
  type: "choice";
  options: Option[];
  multiple?: boolean;
  // Placeholder for the free-text box the "Other" option reveals.
  otherPlaceholder?: string;
}

export type Question = TextQuestion | ChoiceQuestion;
