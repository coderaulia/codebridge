export interface TranslationBreakdown {
  plain_summary: string;
  inputs_and_parameters: string;
  outputs_and_effects: string;
  business_rule_tie_in: string;
  mermaid_diagram: string | null;
  raw_markdown?: string;
  cached: boolean;
}

export interface TranslationStreamEvent {
  event: 'chunk' | 'complete' | 'cached' | 'error';
  content?: string;
  data?: TranslationBreakdown;
  error?: string;
}
