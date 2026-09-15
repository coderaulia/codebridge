"""
CodeBridge V1 - Java Language Parser
Extracts classes, interfaces, records, methods, and Spring Boot REST endpoints with exact line bounds.
"""
import re
from typing import List
from backend.app.parsers.base import BaseParser, ParsedSymbol


class JavaParser(BaseParser):
    """Deterministic symbol parser for Java source code (.java)."""

    # Class declaration: [public] class Name [extends ...] [implements ...] {
    CLASS_REGEX = re.compile(
        r"(?:(?:public|protected|private|abstract|final|static)\s+)*class\s+([A-Za-z0-9_]+)(?:\s+extends\s+[A-Za-z0-9_$.]+)?(?:\s+implements\s+[A-Za-z0-9_$,\s]+)?\s*\{",
        re.MULTILINE,
    )

    # Interface declaration: [public] interface Name [extends ...] {
    INTERFACE_REGEX = re.compile(
        r"(?:(?:public|protected|private)\s+)*interface\s+([A-Za-z0-9_]+)(?:\s+extends\s+[A-Za-z0-9_$,\s]+)?\s*\{",
        re.MULTILINE,
    )

    # Record declaration (Java 16+): [public] record Name(...) {
    RECORD_REGEX = re.compile(
        r"(?:(?:public|protected|private)\s+)*record\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)\s*\{",
        re.MULTILINE,
    )

    # Method declaration: [public|protected|private] [static] [final] ReturnType methodName(...) [throws ...] {
    METHOD_REGEX = re.compile(
        r"(?:(?:public|protected|private|static|final|synchronized|abstract)\s+)+([A-Za-z0-9_<>,.\[\]]+)\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)(?:\s*throws\s+[A-Za-z0-9_,\s]+)?\s*\{",
        re.MULTILINE,
    )

    # Spring mapping annotations
    SPRING_ROUTE_REGEX = re.compile(
        r"@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\s*(?:\(\s*(?:value\s*=\s*|path\s*=\s*)?[\"']?([^\"'\)]*)[\"']?\s*\))?",
        re.MULTILINE,
    )

    def parse(self, code: str, file_path: str = "") -> List[ParsedSymbol]:
        symbols: List[ParsedSymbol] = []

        # Check for class-level @RequestMapping
        class_base_path = ""
        base_match = re.search(r"@RequestMapping\s*\(\s*(?:value\s*=\s*|path\s*=\s*)?[\"']([^\"']+)[\"']", code)
        if base_match:
            class_base_path = base_match.group(1).rstrip("/")

        # 1. Classes
        for match in self.CLASS_REGEX.finditer(code):
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

        # 2. Interfaces
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
                    signature=f"interface {interface_name}",
                )
            )

        # 3. Records
        for match in self.RECORD_REGEX.finditer(code):
            record_name = match.group(1)
            raw_params = match.group(2)
            start_pos = match.start()
            start_line = code.count("\n", 0, start_pos) + 1
            end_line = self._find_closing_brace_line(code, match.end())

            params = self._clean_java_params(raw_params)
            symbols.append(
                ParsedSymbol(
                    name=record_name,
                    symbol_type="model",
                    start_line=start_line,
                    end_line=end_line,
                    signature=f"record {record_name}({', '.join(params)})",
                    parameters=params,
                )
            )

        # 4. Methods & Spring Endpoints
        for match in self.METHOD_REGEX.finditer(code):
            ret_type = match.group(1)
            method_name = match.group(2)
            raw_params = match.group(3)
            start_pos = match.start()
            start_line = code.count("\n", 0, start_pos) + 1
            end_line = self._find_closing_brace_line(code, match.end())

            # Skip constructor matches if method_name is already a keyword or control block
            if method_name in ("if", "for", "while", "switch", "catch"):
                continue

            # Look back up to 5 lines for Spring annotations
            prefix_lines = code[:start_pos].splitlines()[-6:]
            prefix_block = "\n".join(prefix_lines)

            route_match = self.SPRING_ROUTE_REGEX.search(prefix_block)
            params = self._clean_java_params(raw_params)

            if route_match:
                anno = route_match.group(1)
                sub_path = (route_match.group(2) or "").strip("\"' ")
                full_path = f"{class_base_path}/{sub_path.lstrip('/')}".rstrip("/") or "/"
                method = anno.replace("Mapping", "").upper()
                if method == "REQUEST":
                    method = "REST"

                symbols.append(
                    ParsedSymbol(
                        name=f"{method} {full_path}",
                        symbol_type="endpoint",
                        start_line=start_line,
                        end_line=end_line,
                        signature=f"{method} {full_path} -> {ret_type} {method_name}()",
                        parameters=params,
                        metadata={"method": method, "path": full_path, "java_method": method_name},
                    )
                )
            else:
                symbols.append(
                    ParsedSymbol(
                        name=method_name,
                        symbol_type="function",
                        start_line=start_line,
                        end_line=end_line,
                        signature=f"{ret_type} {method_name}({', '.join(params)})",
                        parameters=params,
                    )
                )

        symbols.sort(key=lambda s: s.start_line)
        return symbols

    def _clean_java_params(self, raw_params: str) -> List[str]:
        if not raw_params.strip():
            return []
        items = []
        for p in raw_params.split(","):
            part = p.strip()
            if part:
                # e.g. '@PathVariable String id' or 'Integer count'
                tokens = part.split()
                items.append(tokens[-1] if tokens else part)
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
