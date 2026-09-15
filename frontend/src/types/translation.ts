export interface CrossFileHop {
  target_file_id: string;
  target_path: string;
  target_domain: string;
  target_language: string;
  referenced_symbols: string[];
  relationship_type: string;
}

export interface TranslationBreakdown {
  plain_summary: string;
  inputs_and_parameters: string;
  outputs_and_effects: string;
  business_rule_tie_in: string;
  mermaid_diagram: string | null;
  raw_markdown?: string;
  cross_file_hops?: CrossFileHop[];
  cached: boolean;
}

export interface TranslationStreamEvent {
  event: 'chunk' | 'complete' | 'cached' | 'error';
  content?: string;
  data?: TranslationBreakdown;
  error?: string;
}
