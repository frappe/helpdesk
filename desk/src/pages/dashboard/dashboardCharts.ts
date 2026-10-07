// helpdesk.api.dashboard returns the old experimental chart config shape; these map it to frappe-ui/charts props.
import type {
  BarChartProps,
  ChartValueAxisOptions,
  DonutChartProps,
  NumberCardProps,
  SeriesStyle,
  TimeGrain,
} from "frappe-ui/charts";

type Row = Record<string, unknown>;

interface ValueAxisConfig {
  title?: string;
  yMin?: number;
  yMax?: number;
  echartOptions?: Row;
}

interface SeriesConfig {
  name: string;
  type: "bar" | "line" | "area";
  color?: string;
  axis?: "y" | "y2";
  showDataLabels?: boolean;
  showDataPoints?: boolean;
  lineType?: "solid" | "dashed" | "dotted";
  stackName?: string;
  echartOptions?: Row;
}

export interface AxisChartConfig {
  type: "axis";
  key?: string;
  data?: Row[];
  title?: string;
  subtitle?: string;
  xAxis?: {
    key: string;
    type?: "category" | "time" | "value";
    timeGrain?: TimeGrain;
    title?: string;
    echartOptions?: Row;
  };
  yAxis?: ValueAxisConfig;
  y2Axis?: ValueAxisConfig;
  swapXY?: boolean;
  stacked?: boolean;
  series?: SeriesConfig[];
  echartOptions?: Row;
}

export interface DonutChartConfig {
  type: "pie";
  key?: string;
  data?: Row[];
  title?: string;
  subtitle?: string;
  categoryColumn: string;
  valueColumn: string;
}

export type NumberChartConfig = NumberCardProps & { tooltip?: string };

export type AxisChartKind = "line" | "area" | "bar";

// A rate reads as a whole percent, a duration or rating to one decimal: 84%,
// 0.9 hrs, 4.3/5. The API sends the raw averages.
function roundFor(suffix?: string) {
  const digits = suffix?.trim() === "%" ? 0 : 1;
  return (value: number) =>
    value.toLocaleString("en-US", { maximumFractionDigits: digits });
}

// The API's unit suffixes are plural; one of anything reads singular.
const SINGULAR: Record<string, string> = {
  days: "day",
  hrs: "hr",
  stars: "star",
};

function unitFor(suffix: string | undefined, rounded: string) {
  if (!suffix || rounded !== "1") return suffix;
  return suffix.replace(/(\w+)$/, (word) => SINGULAR[word] ?? word);
}

// Optional chart props reject an explicit undefined, so unset keys are dropped.
function compact<T extends object>(obj: T) {
  return Object.fromEntries(
    Object.entries(obj).filter(([, value]) => value !== undefined)
  ) as { [K in keyof T]?: Exclude<T[K], undefined> };
}

export function toNumberCardProps(
  config: NumberChartConfig,
  deltaCaption?: string
): NumberCardProps {
  const props = { ...config };
  delete props.tooltip;
  const format = roundFor(config.suffix);
  const deltaFormat = roundFor(config.deltaSuffix);
  const value = typeof config.value === "number" ? config.value : null;
  // a change that prints as 0 is no change: no arrow, no red
  const delta =
    config.delta == null
      ? null
      : Number(deltaFormat(Math.abs(config.delta))) === 0
      ? 0
      : config.delta;
  return compact({
    ...props,
    format,
    deltaFormat,
    suffix:
      value === null ? config.suffix : unitFor(config.suffix, format(value)),
    deltaSuffix:
      delta === null
        ? config.deltaSuffix
        : unitFor(config.deltaSuffix, deltaFormat(Math.abs(delta))),
    delta,
    deltaCaption: delta === null ? undefined : deltaCaption,
  }) as NumberCardProps;
}

export function toDonutChartProps(config: DonutChartConfig): DonutChartProps {
  return compact({
    title: config.title,
    subtitle: config.subtitle,
    data: config.data || [],
    category: config.categoryColumn,
    value: config.valueColumn,
  }) as DonutChartProps;
}

export function getAxisChartKind(config: AxisChartConfig): AxisChartKind {
  const types = new Set((config.series || []).map((s) => s.type));
  if (types.size === 1 && types.has("line")) return "line";
  if (types.size === 1 && types.has("area")) return "area";
  return "bar";
}

function toValueAxis(
  axis?: ValueAxisConfig
): ChartValueAxisOptions | undefined {
  return (
    axis &&
    compact({
      title: axis.title,
      min: axis.yMin,
      max: axis.yMax,
      echartOptions: axis.echartOptions,
    })
  );
}

export function toAxisChartProps(config: AxisChartConfig): BarChartProps {
  const series = config.series || [];
  const seriesConfig: Record<string, SeriesStyle> = {};
  series.forEach((s) => {
    seriesConfig[s.name] = compact({
      type: s.type,
      color: s.color,
      showDataLabels: s.showDataLabels,
      showDataPoints: s.showDataPoints,
      dashed: s.lineType === "dashed" || s.lineType === "dotted" || undefined,
      stackName: s.stackName,
      echartOptions: s.echartOptions,
    });
  });

  const y2 = series.filter((s) => s.axis === "y2").map((s) => s.name);
  const horizontal = getAxisChartKind(config) === "bar" && config.swapXY;
  // The old chart drew horizontal bars bottom-up, so the API sends them
  // reversed; frappe-ui/charts draws them top-down.
  const data = horizontal
    ? [...(config.data || [])].reverse()
    : config.data || [];

  const primary = series.filter((s) => s.axis !== "y2").map((s) => s.name);
  const yAxis = toValueAxis(config.yAxis);
  // y2 aligns its ticks to the primary axis; with a fixed y2 range (0-100, 0-5),
  // capping the primary at a multiple of 5 keeps both axes on five clean steps.
  if (
    y2.length &&
    config.y2Axis?.yMax !== undefined &&
    yAxis?.max === undefined
  ) {
    const peak = Math.max(
      0,
      ...data.map((row) => {
        const values = primary.map((key) => Number(row[key]) || 0);
        return config.stacked
          ? values.reduce((a, b) => a + b, 0)
          : Math.max(0, ...values);
      })
    );
    Object.assign(yAxis ?? {}, { max: Math.max(5, Math.ceil(peak / 5) * 5) });
  }

  return compact({
    title: config.title,
    subtitle: config.subtitle,
    data,
    x: config.xAxis?.key as string,
    y: primary,
    y2: y2.length ? y2 : undefined,
    seriesConfig,
    stacked: config.stacked,
    xAxis: compact({
      // a horizontal chart prints the category title under the value axis' 0
      title: horizontal ? undefined : config.xAxis?.title,
      type: config.xAxis?.type,
      timeGrain: config.xAxis?.timeGrain,
      echartOptions: config.xAxis?.echartOptions,
    }),
    yAxis,
    y2Axis: toValueAxis(config.y2Axis),
    echartOptions: config.echartOptions,
    ...(horizontal && { horizontal: true }),
  }) as BarChartProps;
}
