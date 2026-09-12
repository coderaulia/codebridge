"""
CodeBridge V1 - SQL DDL & Migration Parser
Parses SQL files to extract CREATE TABLE statements, columns, types, primary keys, and foreign keys.
"""
import re
import sqlparse
from typing import List, Dict, Any
from backend.app.parsers.base import BaseParser, ParsedSymbol, ParsedSchemaModel


class SqlParser(BaseParser):
    """Deterministic parser for SQL DDL schemas and migration files."""

    CREATE_TABLE_REGEX = re.compile(
        r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"`']?([A-Za-z0-9_]+)[\"`']?\s*\((.*?)\)(?:\s*;|\s*$)",
        re.IGNORECASE | re.DOTALL,
    )

    def parse(self, code: str, file_path: str = "") -> List[ParsedSymbol]:
        """Extracts tables and views from SQL code with exact line ranges."""
        symbols: List[ParsedSymbol] = []

        for match in self.CREATE_TABLE_REGEX.finditer(code):
            table_name = match.group(1)
            start_pos = match.start()
            end_pos = match.end()

            start_line = code.count("\n", 0, start_pos) + 1
            end_line = code.count("\n", 0, end_pos) + 1

            body = match.group(2)
            columns = self._parse_columns(body)

            symbols.append(
                ParsedSymbol(
                    name=table_name,
                    symbol_type="table",
                    start_line=start_line,
                    end_line=end_line,
                    signature=f"CREATE TABLE {table_name}",
                    parameters=[c["name"] for c in columns],
                    metadata={"columns": columns, "schema_type": "sql"},
                )
            )

        return symbols

    def parse_schema_models(self, code: str) -> List[ParsedSchemaModel]:
        """Extracts relational models from SQL tables for ER diagrams."""
        models: List[ParsedSchemaModel] = []

        for match in self.CREATE_TABLE_REGEX.finditer(code):
            table_name = match.group(1)
            start_pos = match.start()
            end_pos = match.end()

            start_line = code.count("\n", 0, start_pos) + 1
            end_line = code.count("\n", 0, end_pos) + 1

            body = match.group(2)
            columns = self._parse_columns(body)

            primary_keys = [c["name"] for c in columns if c.get("is_primary")]
            foreign_keys = []
            relations = []

            for c in columns:
                if c.get("references_table"):
                    fk_info = {
                        "column": c["name"],
                        "target_table": c["references_table"],
                        "target_column": c.get("references_column", "id"),
                    }
                    foreign_keys.append(fk_info)
                    relations.append(
                        {
                            "from_model": table_name,
                            "field": c["name"],
                            "to_model": c["references_table"],
                            "is_list": False,
                        }
                    )

            # Also check explicit FOREIGN KEY (col) REFERENCES other(id)
            fk_regex = re.compile(
                r"FOREIGN\s+KEY\s*\([\s`\"']*([A-Za-z0-9_]+)[\s`\"']*\)\s+REFERENCES\s+[\s`\"']*([A-Za-z0-9_]+)[\s`\"']*\s*\([\s`\"']*([A-Za-z0-9_]+)[\s`\"']*\)",
                re.IGNORECASE,
            )
            for fk_match in fk_regex.finditer(body):
                fk_col = fk_match.group(1)
                ref_table = fk_match.group(2)
                ref_col = fk_match.group(3)
                foreign_keys.append({"column": fk_col, "target_table": ref_table, "target_column": ref_col})
                relations.append({"from_model": table_name, "field": fk_col, "to_model": ref_table, "is_list": False})

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

    def _parse_columns(self, body: str) -> List[Dict[str, Any]]:
        columns = []
        lines = [line.strip() for line in body.split(",\n") if line.strip()]

        if len(lines) <= 1:
            lines = [l.strip() for l in body.splitlines() if l.strip()]

        for raw_line in lines:
            line = raw_line.rstrip(",").strip()
            if not line or line.upper().startswith(("PRIMARY KEY", "CONSTRAINT", "FOREIGN KEY", "UNIQUE KEY", "INDEX", "KEY ")):
                continue

            parts = line.split()
            if not parts:
                continue

            col_name = parts[0].strip("`\"'")
            col_type = parts[1].strip("`\"'") if len(parts) > 1 else "TEXT"

            is_primary = "PRIMARY KEY" in line.upper()
            is_nullable = "NOT NULL" not in line.upper()

            ref_table = None
            ref_col = None
            ref_match = re.search(r"REFERENCES\s+[\"`']?([A-Za-z0-9_]+)[\"`']?\s*(?:\([\s`\"']*([A-Za-z0-9_]+)[\s`\"']*\))?", line, re.IGNORECASE)
            if ref_match:
                ref_table = ref_match.group(1)
                ref_col = ref_match.group(2) if ref_match.group(2) else "id"

            columns.append(
                {
                    "name": col_name,
                    "type": col_type,
                    "is_primary": is_primary,
                    "is_nullable": is_nullable,
                    "references_table": ref_table,
                    "references_column": ref_col,
                    "raw_line": line,
                }
            )

        return columns
