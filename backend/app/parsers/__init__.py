"""
CodeBridge V1 - Parsers Package
Unified parser registry and factory dispatcher for AST & schema analysis.
"""
from pathlib import Path
from typing import Optional
from backend.app.parsers.base import BaseParser
from backend.app.parsers.prisma_parser import PrismaParser
from backend.app.parsers.sql_parser import SqlParser
from backend.app.parsers.python_parser import PythonParser
from backend.app.parsers.ts_js_parser import TsJsParser
from backend.app.parsers.drizzle_parser import DrizzleParser

_PRISMA_PARSER = PrismaParser()
_SQL_PARSER = SqlParser()
_PYTHON_PARSER = PythonParser()
_TS_JS_PARSER = TsJsParser()
_DRIZZLE_PARSER = DrizzleParser()


def get_parser_for_file(file_path: str, code_sample: str = "") -> Optional[BaseParser]:
    """Returns the optimal deterministic parser based on file extension and contents."""
    path = Path(file_path)
    filename = path.name.lower()
    suffix = path.suffix.lower()

    if filename.endswith(".prisma") or suffix == ".prisma":
        return _PRISMA_PARSER

    if suffix == ".sql":
        return _SQL_PARSER

    if suffix in (".py", ".pyw"):
        return _PYTHON_PARSER

    if suffix in (".ts", ".tsx", ".js", ".jsx", ".mjs"):
        # Check if it's a Drizzle schema
        if "pgtable" in code_sample.lower() or "mysqltable" in code_sample.lower() or "sqlitetable" in code_sample.lower():
            return _DRIZZLE_PARSER
        return _TS_JS_PARSER

    return None
