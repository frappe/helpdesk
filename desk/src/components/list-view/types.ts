export type Selection = Set<string>;
export type Key = string;
export type Action = {
  label: string;
  onClick: (key: Key[]) => void;
};
