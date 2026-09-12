"""
CodeBridge V1 - Prisma Schema Parser
Deterministic parser for schema.prisma files. Extracts models, fields, types, and relations.
"""
import re
from typing import List, Dict, Any
from backend.app.parsers.base import BaseParser, ParsedSymbol, ParsedSchemaModel


class PrismaParser(BaseParser):
    """Parses Prisma schema files into structured models and relational links."""

    MODEL_BLOCK_REGEX = re.compile(r"model\s+([A-Za-z0-9_]+)\s*\{([^}]*)\}", re.MULTILINE | re.DOTALL)
    ENUM_BLOCK_REGEX = re.compile(r"enum\s+([A-Za-z0-9_]+)\s*\{([^}]*)\}", re.MULTILINE | re.DOTALL)

    def parse(self, code: str, file_path: str = "") -> List[ParsedSymbol]:
        """Returns ParsedSymbol list for all models and enums with line numbers."""
        symbols: List[ParsedSymbol] = []
        lines = code.splitlines()

        for match in self.MODEL_BLOCK_REGEX.finditer(code):
            model_name = match.group(1)
            start_pos = match.start()
            end_pos = match.end()

            # Calculate 1-indexed line numbers
            start_line = code.count("\n", 0, start_pos) + 1
            end_line = code.count("\n", 0, end_pos) + 1

            body = match.group(2)
            fields = self._parse_fields(body)

            symbols.append(
                ParsedSymbol(
                    name=model_name,
                    symbol_type="model",
                    start_line=start_line,
                    end_line=end_line,
                    signature=f"model {model_name}",
                    parameters=[f["name"] for f in fields],
                    metadata={"fields": fields, "schema_type": "prisma"},
                )
            )

        for match in self.ENUM_BLOCK_REGEX.finditer(code):
            enum_name = match.group(1)
            start_pos = match.start()
            end_pos = match.end()

            start_line = code.count("\n", 0, start_pos) + 1
            end_line = code.count("\n", 0, end_pos) + 1

            symbols.append(
                ParsedSymbol(
                    name=enum_name,
                    symbol_type="enum",
                    start_line=start_line,
                    end_line=end_line,
                    signature=f"enum {enum_name}",
                    metadata={"schema_type": "prisma"},
                )
            )

        return symbols

    def parse_schema_models(self, code: str) -> List[ParsedSchemaModel]:
        """Detailed relational parsing of Prisma models for ER diagrams."""
        models: List[ParsedSchemaModel] = []

        for match in self.MODEL_BLOCK_REGEX.finditer(code):
            model_name = match.group(1)
            start_pos = match.start()
            end_pos = match.end()

            start_line = code.count("\n", 0, start_pos) + 1
            end_line = code.count("\n", 0, end_pos) + 1

            body = match.group(2)
            fields = self._parse_fields(body)

            primary_keys = [f["name"] for f in fields if f.get("is_primary")]
            relations = []
            foreign_keys = []

            for f in fields:
                if f.get("relation"):
                    relations.append(
                        {
                            "from_model": model_name,
                            "field": f["name"],
                            "to_model": f["type"],
                            "is_list": f.get("is_list", False),
                            "details": f.get("relation"),
                        }
                    )
                if f.get("is_foreign_key"):
                    foreign_keys.append(f)

            models.append(
                ParsedSchemaModel(
                    model_name=model_name,
                    fields=fields,
                    primary_keys=primary_keys,
                    foreign_keys=foreign_keys,
                    relations=relations,
                    start_line=start_line,
                    end_line=end_line,
                )
            )

        return models

    def _parse_fields(self, body: str) -> List[Dict[str, Any]]:
        fields = []
        for line in body.splitlines():
            line = line.strip()
            if not line or line.startswith("//") or line.startswith("@@"):
                continue

            parts = line.split()
            if len(parts) < 2:
                continue

            field_name = parts[0]
            field_type_raw = parts[1]

            is_list = field_type_raw.endswith("[]")
            is_optional = field_type_raw.endswith("?")
            clean_type = field_type_raw.rstrip("[]?")

            is_primary = "@id" in line
            is_unique = "@unique" in line

            relation_match = re.search(r"@relation\(([^)]*)\)", line)
            relation_info = relation_match.group(1) if relation_match else None

            fields.append(
                {
                    "name": field_name,
                    "type": clean_type,
                    "is_list": is_list,
                    "is_optional": is_optional,
                    "is_primary": is_primary,
                    "is_unique": is_unique,
                    "relation": relation_info,
                    "is_foreign_key": bool(relation_info and "fields:" in relation_info),
                    "raw_line": line,
                }
            )

        return fields
