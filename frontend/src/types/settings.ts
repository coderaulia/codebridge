export interface ProviderSettings {
  id: string;
  provider_type: 'ollama' | 'lmstudio' | 'deepseek' | 'openrouter' | 'openai' | string;
  base_url: string;
  api_key: string;
  model_name: string;
  temperature: number;
}

export interface ConnectionTestResponse {
  success: boolean;
  latency_ms: number | null;
  message: string;
  available_models?: string[];
}
