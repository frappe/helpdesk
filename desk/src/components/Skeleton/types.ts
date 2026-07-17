export interface SkeletonProps {
  /** Render skeleton while true, the default slot untouched once false. */
  loading?: boolean;
  /** Shape of the standalone bone; ignored when a default slot is given. */
  variant?: "line" | "circle" | "box";
  width?: string;
  height?: string;
}
