"""
CodeBridge V1 - TypeScript / JavaScript Symbol Parser
Extracts functions, React components, classes, interfaces, types, and route handlers.
Employs native Tree-sitter AST queries when available, with robust deterministic fallback.
"""
import re
from typing import List, Optional
from backend.app.parsers.base import BaseParser, ParsedSymbol

# Optional tree-sitter integration
_TREE_SITTER_AVAILABLE = False
try:
    from tree_sitter import Language, Parser
    import tree_sitter_typescript as tstypescript
    _TS_LANGUAGE = Language(tstypescript.language_typescript())
    _TS_PARSER = Parser(_TS_LANGUAGE)
    _TREE_SITTER_AVAILABLE = True
except Exception:
    _TREE_SITTER_AVAILABLE = False


class TsJsParser(BaseParser):
    """Deterministic symbol parser for TypeScript and JavaScript code."""

    # Function declarations: export [async] function name(...) or function name(...)
    FUNC_DECL_REGEX = re.compile(
        r"(?:export\s+)?(?:default\s+)?(?:async\s+)?function(?:\s+([A-Za-z0-9_$]+))?\s*\(([^)]*)\)",
        re.MULTILINE,
    )

    # Next.js / SvelteKit / Hono route exports: export async function GET / POST / PUT / DELETE
    NEXT_ROUTE_REGEX = re.compile(
        r"export\s+(?:async\s+)?function\s+(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s*\(([^)]*)\)",
        re.MULTILINE,
    )

    # Arrow function or component: export const name = [async] (...) => or React.FC
    ARROW_FUNC_REGEX = re.compile(
        r"(?:export\s+)?const\s+([A-Za-z0-9_$]+)\s*(?::\s*[^=]+)?\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z0-9_$]+)\s*(?::\s*[^=]+)?=>",
        re.MULTILINE,
    )

    # Class declaration: export class Name [extends/implements ...] {
    CLASS_DECL_REGEX = re.compile(
        r"(?:export\s+)?(?:default\s+)?class\s+([A-Za-z0-9_$]+)(?:\s+extends\s+[A-Za-z0-9_$.]+)?(?:\s+implements\s+[A-Za-z0-9_$,\s]+)?\s*\{",
        re.MULTILINE,
    )

    # Interface or Type: export interface Name / export type Name
    TYPE_DECL_REGEX = re.compile(
        r"(?:export\s+)?(interface|type)\s+([A-Za-z0-9_$]+)",
        re.MULTILINE,
    )

    # Express / Next / Hono Route handlers: router.get('/path', ...) or app.post('/path', ...)
    ROUTE_HANDLER_REGEX = re.compile(
        r"(?:router|app|server)\.(get|post|put|delete|patch)\s*\(\s*['\"`]([^'\"`]+)['\"`]",
        re.IGNORECASE,
    )

    def parse(self, code: str, file_path: str = "") -> List[ParsedSymbol]:
        # 1. Try Tree-Sitter AST if available
        if _TREE_SITTER_AVAILABLE:
            try:
                symbols = self._parse_tree_sitter(code)
                if symbols:
                    return symbols
            except Exception:
                pass

        # 2. Resilient Deterministic Parsing Fallback
        return self._parse_deterministic(code, file_path)

    def _parse_tree_sitter(self, code: str) -> List[ParsedSymbol]:
        symbols: List[ParsedSymbol] = []
        tree = _TS_PARSER.parse(bytes(code, "utf8"))
        root = tree.root_node

        def walk(node):
            if node.type in ("function_declaration", "generator_function_declaration"):
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = name_node.text.decode("utf8")
                    start_line = node.start_point[0] + 1
                    end_line = node.end_point[0] + 1
                    symbols.append(
                        ParsedSymbol(
                            name=name,
                            symbol_type="function",
                            start_line=start_line,
                            end_line=end_line,
                            signature=f"function {name}()",
                        )
                    )
            elif node.type == "class_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = name_node.text.decode("utf8")
                    symbols.append(
                        ParsedSymbol(
                            name=name,
                            symbol_type="class",
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            signature=f"class {name}",
                        )
                    )
            elif node.type == "interface_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = name_node.text.decode("utf8")
                    symbols.append(
                        ParsedSymbol(
                            name=name,
                            symbol_type="model",
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            signature=f"interface {name}",
                        )
                    )
            for child in node.children:
                walk(child)

        walk(root)
        symbols.sort(key=lambda s: s.start_line)
        return symbols

    def _parse_deterministic(self, code: str, file_path: str = "") -> List[ParsedSymbol]:
        symbols: List[ParsedSymbol] = []
        seen_ranges = set()

        # Next.js Route handlers (GET, POST, etc.)
        for match in self.NEXT_ROUTE_REGEX.finditer(code):
            method = match.group(1).upper()
            start_pos = match.start()
            start_line = code.count("\n", 0, start_pos) + 1
            end_line = self._find_closing_brace_line(code, match.end())

            # Infer route path from file path if possible (e.g. app/api/orders/route.ts -> /api/orders)
            path = self._infer_route_path(file_path) or f"/{method.lower()}"
            symbols.append(
                ParsedSymbol(
                    name=f"{method} {path}",
                    symbol_type="endpoint",
                    start_line=start_line,
                    end_line=end_line,
                    signature=f"export function {method}()",
                    metadata={"method": method, "path": path},
                )
            )
            seen_ranges.add((start_line, end_line))

        # Standard function declarations
        for match in self.FUNC_DECL_REGEX.finditer(code):
            func_name = match.group(1) or "anonymousFunction"
            raw_params = match.group(2) or ""
            start_pos = match.start()
            start_line = code.count("\n", 0, start_pos) + 1
            end_line = self._find_closing_brace_line(code, match.end())

            if (start_line, end_line) in seen_ranges:
                continue

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
            seen_ranges.add((start_line, end_line))

        # Arrow functions & React Components
        for match in self.ARROW_FUNC_REGEX.finditer(code):
            func_name = match.group(1)
            start_pos = match.start()
            start_line = code.count("\n", 0, start_pos) + 1
            end_line = self._find_closing_brace_line(code, match.end())

            if (start_line, end_line) in seen_ranges:
                continue

            # Detect React Component (PascalCase)
            is_component = func_name[0].isupper() if func_name else False
            symbols.append(
                ParsedSymbol(
                    name=func_name,
                    symbol_type="class" if is_component else "function",
                    start_line=start_line,
                    end_line=end_line,
                    signature=f"const {func_name} = (...) =>",
                    metadata={"is_component": is_component},
                )
            )
            seen_ranges.add((start_line, end_line))

        # Classes
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

        # Interfaces & Types
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

        # Express / Hono Route handlers
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

        symbols.sort(key=lambda s: s.start_line)
        return symbols

    def _infer_route_path(self, file_path: str) -> str:
        if not file_path:
            return ""
        # e.g. src/app/api/users/route.ts -> /api/users
        clean = file_path.replace("\\", "/")
        if "api/" in clean:
            idx = clean.find("api/")
            endpoint = "/" + clean[idx:].replace("/route.ts", "").replace("/route.js", "")
            return endpoint
        return ""

    def _find_closing_brace_line(self, code: str, start_index: int, fallback_lines: int = 2) -> int:
        brace_count = 0
        found_first = False
        in_string = None
        start_line = code.count("\n", 0, start_index) + 1

        for i in range(start_index, len(code)):
            char = code[i]
            prev_char = code[i - 1] if i > 0 else ""

            # String literal handling
            if char in ('"', "'", "`") and prev_char != "\\":
                if in_string == char:
                    in_string = None
                elif in_string is None:
                    in_string = char
                continue

            if in_string:
                continue

            if char == "{":
                brace_count += 1
                found_first = True
            elif char == "}":
                brace_count -= 1
                if found_first and brace_count <= 0:
                    return code.count("\n", 0, i) + 1

        return start_line + fallback_lines
