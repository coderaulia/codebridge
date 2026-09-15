"""
CodeBridge V1 - Go Language Parser
Extracts functions, receiver methods, structs, interfaces, and web router endpoints with exact line bounds.
"""
import re
from typing import List
from backend.app.parsers.base import BaseParser, ParsedSymbol


class GoParser(BaseParser):
    """Deterministic symbol parser for Go source code (.go)."""

    # Top-level functions: func FunctionName(params) (returns) {
    FUNC_REGEX = re.compile(
        r"^\s*func\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)",
        re.MULTILINE,
    )

    # Receiver methods: func (r *Receiver) MethodName(params) (returns) {
    METHOD_REGEX = re.compile(
        r"^\s*func\s*\(\s*(?:[A-Za-z0-9_]+\s+)?\*?([A-Za-z0-9_]+)\s*\)\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)",
        re.MULTILINE,
    )

    # Struct definitions: type Name struct {
    STRUCT_REGEX = re.compile(
        r"^\s*type\s+([A-Za-z0-9_]+)\s+struct\s*\{",
        re.MULTILINE,
    )

    # Interface definitions: type Name interface {
    INTERFACE_REGEX = re.compile(
        r"^\s*type\s+([A-Za-z0-9_]+)\s+interface\s*\{",
        re.MULTILINE,
    )

    # Go HTTP Route handlers: (http.HandleFunc, r.GET, router.POST, e.PUT, app.Delete, etc.)
    ROUTE_REGEX = re.compile(
        r"(?:[A-Za-z0-9_]+)\.(HandleFunc|GET|POST|PUT|DELETE|PATCH|Handle|Get|Post|Put|Delete|Patch)\s*\(\s*[\"`]([^\"`]+)[\"`]",
        re.MULTILINE,
    )

    def parse(self, code: str, file_path: str = "") -> List[ParsedSymbol]:
        symbols: List[ParsedSymbol] = []

        # 1. Receiver Methods
        for match in self.METHOD_REGEX.finditer(code):
            receiver_type = match.group(1)
            method_name = match.group(2)
            raw_params = match.group(3)
            start_pos = match.start()
            start_line = code.count("\n", 0, start_pos) + 1
            end_line = self._find_closing_brace_line(code, match.end())

            params = self._clean_params(raw_params)
            symbols.append(
                ParsedSymbol(
                    name=f"({receiver_type}).{method_name}",
                    symbol_type="function",
                    start_line=start_line,
                    end_line=end_line,
                    signature=f"func ({receiver_type}) {method_name}({', '.join(params)})",
                    parameters=params,
                    metadata={"receiver": receiver_type, "method": method_name},
                )
            )

        # 2. Standard Top-level Functions
        for match in self.FUNC_REGEX.finditer(code):
            func_name = match.group(1)
            raw_params = match.group(2)
            start_pos = match.start()
            start_line = code.count("\n", 0, start_pos) + 1
            end_line = self._find_closing_brace_line(code, match.end())

            params = self._clean_params(raw_params)
            symbols.append(
                ParsedSymbol(
                    name=func_name,
                    symbol_type="function",
                    start_line=start_line,
                    end_line=end_line,
                    signature=f"func {func_name}({', '.join(params)})",
                    parameters=params,
                )
            )

        # 3. Structs
        for match in self.STRUCT_REGEX.finditer(code):
            struct_name = match.group(1)
            start_pos = match.start()
            start_line = code.count("\n", 0, start_pos) + 1
            end_line = self._find_closing_brace_line(code, match.end())

            symbols.append(
                ParsedSymbol(
                    name=struct_name,
                    symbol_type="model",
                    start_line=start_line,
                    end_line=end_line,
                    signature=f"type {struct_name} struct",
                )
            )

        # 4. Interfaces
        for match in self.INTERFACE_REGEX.finditer(code):
            interface_name = match.group(1)
            start_pos = match.start()
            start_line = code.count("\n", 0, start_pos) + 1
            end_line = self._find_closing_brace_line(code, match.end())

            symbols.append(
                ParsedSymbol(
                    name=interface_name,
                    symbol_type="model",
                    start_line=start_line,
                    end_line=end_line,
                    signature=f"type {interface_name} interface",
                )
            )

        # 5. Route Handlers
        for match in self.ROUTE_REGEX.finditer(code):
            method = match.group(1).upper()
            if method in ("HANDLEFUNC", "HANDLE"):
                method = "HTTP"
            path = match.group(2)
            start_pos = match.start()
            start_line = code.count("\n", 0, start_pos) + 1
            end_line = self._find_statement_end_line(code, match.end())

            symbols.append(
                ParsedSymbol(
                    name=f"{method} {path}",
                    symbol_type="endpoint",
                    start_line=start_line,
                    end_line=end_line,
                    signature=f"{method} {path}",
                    metadata={"method": method, "path": path},
                )
            )

        symbols.sort(key=lambda s: s.start_line)
        return symbols

    def _clean_params(self, raw_params: str) -> List[str]:
        """Cleans Go parameter list (e.g. 'w http.ResponseWriter, req *http.Request')."""
        if not raw_params.strip():
            return []
        items = []
        for p in raw_params.split(","):
            part = p.strip()
            if part:
                tokens = part.split()
                items.append(tokens[0] if tokens else part)
        return items

    def _find_closing_brace_line(self, code: str, start_index: int, fallback_lines: int = 2) -> int:
        brace_count = 0
        found_first = False
        start_line = code.count("\n", 0, start_index) + 1

        for i in range(start_index, len(code)):
            char = code[i]
            if char == "{":
                brace_count += 1
                found_first = True
            elif char == "}":
                brace_count -= 1
                if found_first and brace_count <= 0:
                    return code.count("\n", 0, i) + 1

        return start_line + fallback_lines

    def _find_statement_end_line(self, code: str, start_index: int) -> int:
        paren_count = 1
        start_line = code.count("\n", 0, start_index) + 1

        for i in range(start_index, len(code)):
            char = code[i]
            if char == "(":
                paren_count += 1
            elif char == ")":
                paren_count -= 1
                if paren_count <= 0:
                    return code.count("\n", 0, i) + 1
            elif char == "\n" and paren_count <= 0:
                return code.count("\n", 0, i) + 1

        return start_line
