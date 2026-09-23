export interface LayoutItemRequired {
  w: number
  h: number
  x: number
  y: number
  i: number | string
}

export interface LayoutItem extends LayoutItemRequired {
  minW?: number
  minH?: number
  maxW?: number
  maxH?: number
  moved?: boolean
  static?: boolean
  isDraggable?: boolean
  isResizable?: boolean
}

export type Layout = Array<LayoutItem>

export interface GridLayoutProps {
  cols?: number
  rowHeight?: number
  disabled?: Boolean
}
