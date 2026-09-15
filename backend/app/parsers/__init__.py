"""
CodeBridge V1 - Parsers Package
Unified parser registry and factory dispatcher for AST & schema analysis.
Supports TypeScript/JavaScript, Python, Go, Rust, Java, Prisma, SQL DDL, Drizzle, and OpenAPI.
"""
from pathlib import Path
from typing import Optional
from backend.app.parsers.base import BaseParser
from backend.app.parsers.prisma_parser import PrismaParser
from backend.app.parsers.sql_parser import SqlParser
from backend.app.parsers.python_parser import PythonParser
from backend.app.parsers.ts_js_parser import TsJsParser
from backend.app.parsers.drizzle_parser import DrizzleParser
from backend.app.parsers.go_parser import GoParser
from backend.app.parsers.rust_parser import RustParser
from backend.app.parsers.java_parser import JavaParser
from backend.app.parsers.openapi_parser import OpenApiParser

_PRISMA_PARSER = PrismaParser()
_SQL_PARSER = SqlParser()
_PYTHON_PARSER = PythonParser()
_TS_JS_PARSER = TsJsParser()
_DRIZZLE_PARSER = DrizzleParser()
_GO_PARSER = GoParser()
_RUST_PARSER = RustParser()
_JAVA_PARSER = JavaParser()
_OPENAPI_PARSER = OpenApiParser()


def get_parser_for_file(file_path: str, code_sample: str = "") -> Optional[BaseParser]:
    """Returns the optimal deterministic parser based on file extension and contents."""
    path = Path(file_path)
    filename = path.name.lower()
    suffix = path.suffix.lower()

    # OpenAPI / Swagger specifications
    if any(k in filename for k in ("openapi", "swagger")) and suffix in (".json", ".yaml", ".yml"):
        return _OPENAPI_PARSER
    if suffix in (".json", ".yaml", ".yml") and any(k in code_sample.lower()[:300] for k in ("openapi:", "swagger:", '"openapi"', '"swagger"')):
        return _OPENAPI_PARSER

    # Prisma Schema
    if filename.endswith(".prisma") or suffix == ".prisma":
        return _PRISMA_PARSER

    # SQL DDL
    if suffix == ".sql":
        return _SQL_PARSER

    # Python
    if suffix in (".py", ".pyw"):
        return _PYTHON_PARSER

    # Go
    if suffix == ".go":
        return _GO_PARSER

    # Rust
    if suffix == ".rs":
        return _RUST_PARSER

    # Java
    if suffix == ".java":
        return _JAVA_PARSER

    # TypeScript / JavaScript
    if suffix in (".ts", ".tsx", ".js", ".jsx", ".mjs"):
        if "pgtable" in code_sample.lower() or "mysqltable" in code_sample.lower() or "sqlitetable" in code_sample.lower():
            return _DRIZZLE_PARSER
        return _TS_JS_PARSER

    return None
