export interface AIFeatureConfig {
  summary?: SummaryConfig;
}

export interface SummaryConfig {
  llm: string;
  enabled: boolean;
  directive: string;
}
