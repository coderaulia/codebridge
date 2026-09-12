"""
CodeBridge V1 - TypeScript / JavaScript Symbol Parser
Extracts exported functions, classes, interfaces, types, and route handlers with exact line boundaries.
"""
import re
from typing import List
from backend.app.parsers.base import BaseParser, ParsedSymbol


class TsJsParser(BaseParser):
    """Deterministic symbol parser for TypeScript and JavaScript code."""

    # Function patterns: export [async] function name(...) or [async] function name(...)
    FUNC_DECL_REGEX = re.compile(
        r"(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(([^)]*)\)",
        re.MULTILINE,
    )

    # Arrow function or function expression: export const name = [async] (...) =>
    ARROW_FUNC_REGEX = re.compile(
        r"(?:export\s+)?const\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*(?::\s*[^=]+)?=>",
        re.MULTILINE,
    )

    # Class declaration: export class Name [extends/implements ...] {
    CLASS_DECL_REGEX = re.compile(
        r"(?:export\s+)?(?:default\s+)?class\s+([A-Za-z0-9_$]+)(?:\s+extends\s+[A-Za-z0-9_$.]+)?(?:\s+implements\s+[A-Za-z0-9_$,\s]+)?\s*\{",
        re.MULTILINE,
    )

    # Interface or Type: export interface Name / export type Name
    TYPE_DECL_REGEX = re.compile(
        r"export\s+(interface|type)\s+([A-Za-z0-9_$]+)",
        re.MULTILINE,
    )

    # Express / Next / Hono Route handlers: router.get('/path', ...) or app.post('/path', ...)
    ROUTE_HANDLER_REGEX = re.compile(
        r"(?:router|app)\.(get|post|put|delete|patch)\s*\(\s*['\"`]([^'\"`]+)['\"`]",
        re.IGNORECASE,
    )

    def parse(self, code: str, file_path: str = "") -> List[ParsedSymbol]:
        symbols: List[ParsedSymbol] = []
        lines = code.splitlines()

        # 1. Standard function declarations
        for match in self.FUNC_DECL_REGEX.finditer(code):
            func_name = match.group(1)
            raw_params = match.group(2)
            start_pos = match.start()
            start_line = code.count("\n", 0, start_pos) + 1
            end_line = self._find_closing_brace_line(code, match.end())

            params = [p.split(":")[0].strip() for p in raw_params.split(",") if p.strip()]
            symbols.append(
                ParsedSymbol(
                    name=func_name,
                    symbol_type="function",
                    start_line=start_line,
                    end_line=end_line,
                    signature=f"function {func_name}({', '.join(params)})",
                    parameters=params,
                )
            )

        # 2. Arrow functions assigned to const
        for match in self.ARROW_FUNC_REGEX.finditer(code):
            func_name = match.group(1)
            raw_params = match.group(2)
            start_pos = match.start()
            start_line = code.count("\n", 0, start_pos) + 1
            end_line = self._find_closing_brace_line(code, match.end())

            params = [p.split(":")[0].strip() for p in raw_params.split(",") if p.strip()]
            symbols.append(
                ParsedSymbol(
                    name=func_name,
                    symbol_type="function",
                    start_line=start_line,
                    end_line=end_line,
                    signature=f"const {func_name} = ({', '.join(params)}) =>",
                    parameters=params,
                )
            )

        # 3. Class declarations
        for match in self.CLASS_DECL_REGEX.finditer(code):
            class_name = match.group(1)
            start_pos = match.start()
            start_line = code.count("\n", 0, start_pos) + 1
            end_line = self._find_closing_brace_line(code, match.end())

            symbols.append(
                ParsedSymbol(
                    name=class_name,
                    symbol_type="class",
                    start_line=start_line,
                    end_line=end_line,
                    signature=f"class {class_name}",
                )
            )

        # 4. Interface and Type declarations
        for match in self.TYPE_DECL_REGEX.finditer(code):
            kind = match.group(1)
            type_name = match.group(2)
            start_pos = match.start()
            start_line = code.count("\n", 0, start_pos) + 1
            end_line = self._find_closing_brace_line(code, match.end(), fallback_lines=5)

            symbols.append(
                ParsedSymbol(
                    name=type_name,
                    symbol_type="model" if kind == "interface" else "type",
                    start_line=start_line,
                    end_line=end_line,
                    signature=f"{kind} {type_name}",
                )
            )

        # 5. Route handlers
        for match in self.ROUTE_HANDLER_REGEX.finditer(code):
            method = match.group(1).upper()
            route_path = match.group(2)
            start_pos = match.start()
            start_line = code.count("\n", 0, start_pos) + 1
            end_line = self._find_closing_brace_line(code, match.end(), fallback_lines=10)

            symbols.append(
                ParsedSymbol(
                    name=f"{method} {route_path}",
                    symbol_type="endpoint",
                    start_line=start_line,
                    end_line=end_line,
                    signature=f"{method} {route_path}",
                    metadata={"method": method, "path": route_path},
                )
            )

        # Sort symbols by start_line
        symbols.sort(key=lambda s: s.start_line)
        return symbols

    def _find_closing_brace_line(self, code: str, start_index: int, fallback_lines: int = 1) -> int:
        """Finds matching closing curly brace from start_index, or returns reasonable estimate."""
        brace_count = 0
        found_first = False
        lines_count_at_start = code.count("\n", 0, start_index) + 1

        for i in range(start_index, len(code)):
            char = code[i]
            if char == "{":
                brace_count += 1
                found_first = True
            elif char == "}":
                brace_count -= 1
                if found_first and brace_count <= 0:
                    return code.count("\n", 0, i) + 1

        return lines_count_at_start + fallback_lines
