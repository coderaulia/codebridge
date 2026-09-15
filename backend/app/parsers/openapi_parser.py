"""
CodeBridge V1 - OpenAPI & Swagger Specification Parser
Extracts API endpoints, parameters, and schema models from openapi.json, openapi.yaml, and swagger files.
Supports generating ParsedSchemaModel for visual Mermaid ER diagrams.
"""
import json
import re
from typing import List, Dict, Any, Optional
import yaml

from backend.app.parsers.base import BaseParser, ParsedSymbol, ParsedSchemaModel


class OpenApiParser(BaseParser):
    """Deterministic parser for OpenAPI 3.x and Swagger 2.0 specifications."""

    HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head"}

    def parse(self, code: str, file_path: str = "") -> List[ParsedSymbol]:
        data = self._load_doc(code)
        if not data or not isinstance(data, dict):
            return []

        symbols: List[ParsedSymbol] = []
        paths = data.get("paths", {})

        # 1. Parse Paths & Operations
        if isinstance(paths, dict):
            for path_str, path_item in paths.items():
                if not isinstance(path_item, dict):
                    continue

                for method, op in path_item.items():
                    if method.lower() not in self.HTTP_METHODS or not isinstance(op, dict):
                        continue

                    method_upper = method.upper()
                    op_id = op.get("operationId", "")
                    summary = op.get("summary") or op.get("description", "")
                    tags = op.get("tags", [])
                    parameters = [p.get("name", "") for p in op.get("parameters", []) if isinstance(p, dict)]

                    # Find line number in original code
                    start_line, end_line = self._find_path_lines(code, path_str, method)

                    signature = f"{method_upper} {path_str}"
                    if op_id:
                        signature += f" ({op_id})"

                    symbols.append(
                        ParsedSymbol(
                            name=f"{method_upper} {path_str}",
                            symbol_type="endpoint",
                            start_line=start_line,
                            end_line=end_line,
                            signature=signature,
                            parameters=parameters,
                            docstring=summary,
                            metadata={
                                "method": method_upper,
                                "path": path_str,
                                "operationId": op_id,
                                "tags": tags,
                            },
                        )
                    )

        # 2. Parse Schema Definitions / Models as symbols
        schemas = self._extract_schemas_dict(data)
        for schema_name, schema_obj in schemas.items():
            if not isinstance(schema_obj, dict):
                continue
            start_line, end_line = self._find_schema_lines(code, schema_name)
            props = list(schema_obj.get("properties", {}).keys())

            symbols.append(
                ParsedSymbol(
                    name=schema_name,
                    symbol_type="model",
                    start_line=start_line,
                    end_line=end_line,
                    signature=f"schema {schema_name}",
                    parameters=props,
                    metadata={"schema_type": "openapi"},
                )
            )

        symbols.sort(key=lambda s: s.start_line)
        return symbols

    def parse_schema_models(self, code: str) -> List[ParsedSchemaModel]:
        """Extracts relational models from OpenAPI schemas for Mermaid ER diagrams."""
        data = self._load_doc(code)
        if not data or not isinstance(data, dict):
            return []

        models: List[ParsedSchemaModel] = []
        schemas = self._extract_schemas_dict(data)

        for model_name, model_def in schemas.items():
            if not isinstance(model_def, dict):
                continue

            properties = model_def.get("properties", {})
            required_fields = set(model_def.get("required", []))
            start_line, end_line = self._find_schema_lines(code, model_name)

            fields: List[Dict[str, Any]] = []
            relations: List[Dict[str, Any]] = []
            primary_keys: List[str] = []

            for prop_name, prop_def in properties.items():
                if not isinstance(prop_def, dict):
                    continue

                prop_type = prop_def.get("type", "string")
                is_list = prop_type == "array"
                ref = prop_def.get("$ref") or (prop_def.get("items", {}).get("$ref") if is_list else None)

                ref_target = None
                if ref:
                    ref_target = ref.split("/")[-1]
                    relations.append(
                        {
                            "from_model": model_name,
                            "field": prop_name,
                            "to_model": ref_target,
                            "is_list": is_list,
                        }
                    )

                is_pk = prop_name.lower() in ("id", f"{model_name.lower()}_id")
                if is_pk:
                    primary_keys.append(prop_name)

                fields.append(
                    {
                        "name": prop_name,
                        "type": ref_target if ref_target else prop_type,
                        "is_primary": is_pk,
                        "is_nullable": prop_name not in required_fields,
                        "is_list": is_list,
                        "references_table": ref_target,
                    }
                )

            models.append(
                ParsedSchemaModel(
                    model_name=model_name,
                    fields=fields,
                    primary_keys=primary_keys,
                    foreign_keys=[],
                    relations=relations,
                    start_line=start_line,
                    end_line=end_line,
                )
            )

        return models

    def _load_doc(self, code: str) -> Optional[Dict[str, Any]]:
        clean = code.strip()
        if not clean:
            return None
        # Try JSON
        if clean.startswith("{"):
            try:
                return json.loads(code)
            except Exception:
                pass
        # Try YAML
        try:
            return yaml.safe_load(code)
        except Exception:
            return None

    def _extract_schemas_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # OpenAPI 3.x
        components = data.get("components", {})
        if isinstance(components, dict) and "schemas" in components:
            return components["schemas"]
        # Swagger 2.0
        if "definitions" in data and isinstance(data["definitions"], dict):
            return data["definitions"]
        return {}

    def _find_path_lines(self, code: str, path_str: str, method: str) -> tuple[int, int]:
        pattern = re.compile(rf"['\"]?{re.escape(path_str)}['\"]?", re.IGNORECASE)
        match = pattern.search(code)
        if match:
            start_line = code.count("\n", 0, match.start()) + 1
            return start_line, start_line + 10
        return 1, 10

    def _find_schema_lines(self, code: str, schema_name: str) -> tuple[int, int]:
        pattern = re.compile(rf"['\"]?{re.escape(schema_name)}['\"]?\s*:", re.IGNORECASE)
        match = pattern.search(code)
        if match:
            start_line = code.count("\n", 0, match.start()) + 1
            return start_line, start_line + 15
        return 1, 15
