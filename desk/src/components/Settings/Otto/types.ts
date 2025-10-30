export interface SmartFeatureConfig {
  summary?: SummaryConfig;
}

export interface SummaryConfig {
  llm: string;
  enabled: boolean;
  guidelines: string;
}

export interface OttoModel {
  name: string;
  title: string;
  provider: string;
  size: string;
  is_reasoning: boolean;
  supports_vision: boolean;
  is_enabled: boolean;
  is_api_key_set: boolean;
}
