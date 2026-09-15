"""
CodeBridge V1 - Rust Language Parser
Extracts functions, structs, enums, impl blocks, and web route handlers with exact line bounds.
"""
import re
from typing import List
from backend.app.parsers.base import BaseParser, ParsedSymbol


class RustParser(BaseParser):
    """Deterministic symbol parser for Rust source code (.rs)."""

    # Functions: [pub] [async] [const] fn name(...) [-> ReturnType] {
    FN_REGEX = re.compile(
        r"(?:(?:pub(?:\s*\([^\)]*\))?)\s+)?(?:async\s+)?(?:const\s+)?fn\s+([A-Za-z0-9_]+)\s*(?:<[^>]*>)?\s*\(([^)]*)\)",
        re.MULTILINE,
    )

    # Structs: [pub] struct Name [<...>] [{;]
    STRUCT_REGEX = re.compile(
        r"(?:(?:pub(?:\s*\([^\)]*\))?)\s+)?struct\s+([A-Za-z0-9_]+)(?:\s*<[^>]*>)?(?:\s*\{|\s*\([^)]*\)\s*;|\s*;)",
        re.MULTILINE,
    )

    # Enums: [pub] enum Name [<...>] {
    ENUM_REGEX = re.compile(
        r"(?:(?:pub(?:\s*\([^\)]*\))?)\s+)?enum\s+([A-Za-z0-9_]+)(?:\s*<[^>]*>)?\s*\{",
        re.MULTILINE,
    )

    # Impl blocks: impl [<...>] [Trait for] Name [<...>] {
    IMPL_REGEX = re.compile(
        r"^\s*impl(?:\s*<[^>]*>)?\s+(?:([A-Za-z0-9_:]+)\s+for\s+)?([A-Za-z0-9_:]+)(?:\s*<[^>]*>)?\s*\{",
        re.MULTILINE,
    )

    # Actix / Rocket route macro: #[get("/path")] or #[post("/path")]
    MACRO_ROUTE_REGEX = re.compile(
        r"#\[(get|post|put|delete|patch)\s*\(\s*\"([^\"]+)\"\s*\)\]",
        re.IGNORECASE | re.MULTILINE,
    )

    # Axum route definition: .route("/path", get(handler))
    AXUM_ROUTE_REGEX = re.compile(
        r"\.route\s*\(\s*\"([^\"]+)\"\s*,\s*(get|post|put|delete|patch)\s*\(",
        re.IGNORECASE | re.MULTILINE,
    )

    def parse(self, code: str, file_path: str = "") -> List[ParsedSymbol]:
        symbols: List[ParsedSymbol] = []

        # 1. Functions
        for match in self.FN_REGEX.finditer(code):
            fn_name = match.group(1)
            raw_params = match.group(2)
            start_pos = match.start()
            start_line = code.count("\n", 0, start_pos) + 1
            end_line = self._find_closing_brace_line(code, match.end())

            # Check if immediately preceded by an actix route macro
            prefix = code[:start_pos]
            last_lines = prefix.strip().splitlines()
            route_info = None
            if last_lines:
                last_line = last_lines[-1].strip()
                macro_m = self.MACRO_ROUTE_REGEX.search(last_line)
                if macro_m:
                    route_info = (macro_m.group(1).upper(), macro_m.group(2))

            params = self._clean_rust_params(raw_params)
            sym_type = "endpoint" if route_info else "function"
            name = f"{route_info[0]} {route_info[1]}" if route_info else fn_name

            symbols.append(
                ParsedSymbol(
                    name=name,
                    symbol_type=sym_type,
                    start_line=start_line,
                    end_line=end_line,
                    signature=f"fn {fn_name}({', '.join(params)})",
                    parameters=params,
                    metadata={"route": route_info} if route_info else {},
                )
            )

        # 2. Structs
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
                    signature=f"struct {struct_name}",
                )
            )

        # 3. Enums
        for match in self.ENUM_REGEX.finditer(code):
            enum_name = match.group(1)
            start_pos = match.start()
            start_line = code.count("\n", 0, start_pos) + 1
            end_line = self._find_closing_brace_line(code, match.end())

            symbols.append(
                ParsedSymbol(
                    name=enum_name,
                    symbol_type="model",
                    start_line=start_line,
                    end_line=end_line,
                    signature=f"enum {enum_name}",
                )
            )

        # 4. Impl blocks
        for match in self.IMPL_REGEX.finditer(code):
            trait_name = match.group(1)
            target_name = match.group(2)
            start_pos = match.start()
            start_line = code.count("\n", 0, start_pos) + 1
            end_line = self._find_closing_brace_line(code, match.end())

            name = f"impl {trait_name} for {target_name}" if trait_name else f"impl {target_name}"
            symbols.append(
                ParsedSymbol(
                    name=name,
                    symbol_type="class",
                    start_line=start_line,
                    end_line=end_line,
                    signature=name,
                )
            )

        # 5. Axum Routes
        for match in self.AXUM_ROUTE_REGEX.finditer(code):
            path = match.group(1)
            method = match.group(2).upper()
            start_pos = match.start()
            start_line = code.count("\n", 0, start_pos) + 1
            end_line = code.count("\n", 0, match.end()) + 1

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

    def _clean_rust_params(self, raw_params: str) -> List[str]:
        if not raw_params.strip():
            return []
        items = []
        for p in raw_params.split(","):
            part = p.strip()
            if part:
                tokens = part.split(":")
                items.append(tokens[0].strip())
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
