"""
CodeBridge V1 - Python AST Symbol Parser
Uses Python's native ast module to extract classes, functions, decorators, and FastAPI endpoints.
"""
import ast
import textwrap
from typing import List
from backend.app.parsers.base import BaseParser, ParsedSymbol


class PythonParser(BaseParser):
    """Deterministic parser extracting Python functions, classes, and endpoints."""

    def parse(self, code: str, file_path: str = "") -> List[ParsedSymbol]:
        symbols: List[ParsedSymbol] = []
        try:
            tree = ast.parse(textwrap.dedent(code))
        except (SyntaxError, Exception):
            return symbols

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                symbols.append(self._parse_function(node, code))
            elif isinstance(node, ast.ClassDef):
                symbols.append(self._parse_class(node, code))
                # Also extract methods within the class
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_symbol = self._parse_function(item, code, parent_class=node.name)
                        symbols.append(method_symbol)

        return symbols

    def _parse_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, code: str, parent_class: str = "") -> ParsedSymbol:
        # Determine if it's an API route based on decorators
        decorators = []
        is_endpoint = False
        for d in node.decorator_list:
            if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute):
                dec_name = f"{d.func.attr}"
                decorators.append(dec_name)
                if dec_name.lower() in ("get", "post", "put", "delete", "patch", "route"):
                    is_endpoint = True
            elif isinstance(d, ast.Name):
                decorators.append(d.id)

        params = [arg.arg for arg in node.args.args]
        docstring = ast.get_docstring(node)

        name = f"{parent_class}.{node.name}" if parent_class else node.name
        symbol_type = "endpoint" if is_endpoint else "function"

        # End line support
        end_line = getattr(node, "end_lineno", node.lineno)

        return ParsedSymbol(
            name=name,
            symbol_type=symbol_type,
            start_line=node.lineno,
            end_line=end_line,
            signature=f"def {node.name}({', '.join(params)})",
            parameters=params,
            docstring=docstring,
            metadata={"decorators": decorators, "parent_class": parent_class, "is_async": isinstance(node, ast.AsyncFunctionDef)},
        )

    def _parse_class(self, node: ast.ClassDef, code: str) -> ParsedSymbol:
        docstring = ast.get_docstring(node)
        bases = []
        for b in node.bases:
            if isinstance(b, ast.Name):
                bases.append(b.id)
            elif isinstance(b, ast.Attribute):
                bases.append(b.attr)

        end_line = getattr(node, "end_lineno", node.lineno)

        return ParsedSymbol(
            name=node.name,
            symbol_type="class",
            start_line=node.lineno,
            end_line=end_line,
            signature=f"class {node.name}({', '.join(bases)})" if bases else f"class {node.name}",
            parameters=bases,
            docstring=docstring,
            metadata={"bases": bases},
        )
