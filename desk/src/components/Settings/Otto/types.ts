export interface SmartFeatureConfig {
  summary?: SummaryConfig;
}

export interface SummaryConfig {
  llm: string;
  enabled: boolean;
  guidelines: string;
}
