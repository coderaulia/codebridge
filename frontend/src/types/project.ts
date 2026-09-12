export interface Project {
  id: string;
  name: string;
  source_type: 'local' | 'github';
  source_path: string;
  executive_summary: string | null;
  created_at: string;
  updated_at: string;
}

export interface FileRecord {
  id: string;
  project_id: string;
  relative_path: string;
  file_type: 'code' | 'schema' | 'config' | 'doc' | 'other';
  language: string;
  size_bytes: number;
  plain_summary: string | null;
  business_domain: string | null;
}

export interface SymbolRecord {
  id: string;
  file_id: string;
  name: string;
  symbol_type: 'function' | 'class' | 'model' | 'table' | 'endpoint';
  start_line: number;
  end_line: number;
  signature: string | null;
  parameters_json: string | null;
}

export interface FileDetail extends FileRecord {
  content: string;
  symbols: SymbolRecord[];
}

export interface BusinessDomainGroup {
  domain_name: string;
  files: FileRecord[];
}
