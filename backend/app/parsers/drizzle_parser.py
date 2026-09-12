"""
CodeBridge V1 - Drizzle ORM Schema Parser
Parses TypeScript Drizzle ORM schemas (pgTable, mysqlTable, sqliteTable) and relations.
"""
import re
from typing import List, Dict, Any
from backend.app.parsers.base import BaseParser, ParsedSymbol, ParsedSchemaModel


class DrizzleParser(BaseParser):
    """Deterministic parser for Drizzle ORM schema definitions."""

    TABLE_REGEX = re.compile(
        r"export\s+const\s+([A-Za-z0-9_$]+)\s*=\s*(?:pgTable|mysqlTable|sqliteTable)\s*\(\s*['\"`]([^'\"`]+)['\"`]\s*,\s*\{([^}]*)\}",
        re.MULTILINE | re.DOTALL,
    )

    RELATIONS_REGEX = re.compile(
        r"export\s+const\s+([A-Za-z0-9_$]+)\s*=\s*relations\s*\(\s*([A-Za-z0-9_$]+)\s*,\s*\(.*?\)\s*=>\s*\((\{.*?\})\)\s*\)",
        re.MULTILINE | re.DOTALL,
    )

    def parse(self, code: str, file_path: str = "") -> List[ParsedSymbol]:
        symbols: List[ParsedSymbol] = []

        for match in self.TABLE_REGEX.finditer(code):
            var_name = match.group(1)
            table_name = match.group(2)
            body = match.group(3)

            start_pos = match.start()
            end_pos = match.end()

            start_line = code.count("\n", 0, start_pos) + 1
            end_line = code.count("\n", 0, end_pos) + 1

            columns = self._parse_drizzle_columns(body)

            symbols.append(
                ParsedSymbol(
                    name=table_name,
                    symbol_type="table",
                    start_line=start_line,
                    end_line=end_line,
                    signature=f"drizzle table: {table_name} ({var_name})",
                    parameters=[c["name"] for c in columns],
                    metadata={"columns": columns, "var_name": var_name, "schema_type": "drizzle"},
                )
            )

        return symbols

    def parse_schema_models(self, code: str) -> List[ParsedSchemaModel]:
        models: List[ParsedSchemaModel] = []

        for match in self.TABLE_REGEX.finditer(code):
            var_name = match.group(1)
            table_name = match.group(2)
            body = match.group(3)

            start_pos = match.start()
            end_pos = match.end()

            start_line = code.count("\n", 0, start_pos) + 1
            end_line = code.count("\n", 0, end_pos) + 1

            columns = self._parse_drizzle_columns(body)
            primary_keys = [c["name"] for c in columns if c.get("is_primary")]
            foreign_keys = [c for c in columns if c.get("references_table")]

            relations = []
            for c in foreign_keys:
                relations.append(
                    {
                        "from_model": table_name,
                        "field": c["name"],
                        "to_model": c["references_table"],
                        "is_list": False,
                    }
                )

            models.append(
                ParsedSchemaModel(
                    model_name=table_name,
                    fields=columns,
                    primary_keys=primary_keys,
                    foreign_keys=foreign_keys,
                    relations=relations,
                    start_line=start_line,
                    end_line=end_line,
                )
            )

        return models

    def _parse_drizzle_columns(self, body: str) -> List[Dict[str, Any]]:
        columns = []
        for line in body.splitlines():
            line = line.strip()
            if not line or line.startswith("//"):
                continue

            col_match = re.match(r"([A-Za-z0-9_$]+)\s*:\s*([A-Za-z0-9_$]+)\s*\(\s*['\"`]([^'\"`]+)['\"`]\s*\)(.*)", line)
            if col_match:
                field_key = col_match.group(1)
                col_type = col_match.group(2)
                db_col_name = col_match.group(3)
                chain = col_match.group(4)

                is_primary = ".primaryKey()" in chain
                is_nullable = ".notNull()" not in chain

                ref_match = re.search(r"\.references\(\s*\(\)\s*=>\s*([A-Za-z0-9_$]+)\.([A-Za-z0-9_$]+)\s*\)", chain)
                ref_table = ref_match.group(1) if ref_match else None
                ref_col = ref_match.group(2) if ref_match else None

                columns.append(
                    {
                        "name": db_col_name or field_key,
                        "field_key": field_key,
                        "type": col_type,
                        "is_primary": is_primary,
                        "is_nullable": is_nullable,
                        "references_table": ref_table,
                        "references_column": ref_col,
                        "raw_line": line,
                    }
                )

        return columns
