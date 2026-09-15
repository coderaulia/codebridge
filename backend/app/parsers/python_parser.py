"""
CodeBridge V1 - Python AST Symbol Parser
Uses Python's native ast module to extract classes, Pydantic models, functions, and FastAPI/Flask endpoints.
"""
import ast
import textwrap
from typing import List, Tuple, Optional
from backend.app.parsers.base import BaseParser, ParsedSymbol


class PythonParser(BaseParser):
    """Deterministic parser extracting Python functions, classes, models, and endpoints."""

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
                # Extract methods within the class
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_symbol = self._parse_function(item, code, parent_class=node.name)
                        symbols.append(method_symbol)

        return symbols

    def _parse_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, code: str, parent_class: str = "") -> ParsedSymbol:
        decorators = []
        endpoint_info: Optional[Tuple[str, str]] = None  # (method, path)

        for d in node.decorator_list:
            if isinstance(d, ast.Call):
                dec_func = d.func
                dec_attr = ""
                if isinstance(dec_func, ast.Attribute):
                    dec_attr = dec_func.attr.lower()
                    decorators.append(f"{dec_func.attr}")
                elif isinstance(dec_func, ast.Name):
                    dec_attr = dec_func.id.lower()
                    decorators.append(dec_func.id)

                if dec_attr in ("get", "post", "put", "delete", "patch", "route"):
                    # Extract path from first argument if string literal
                    route_path = "/"
                    if d.args and isinstance(d.args[0], ast.Constant) and isinstance(d.args[0].value, str):
                        route_path = d.args[0].value
                    endpoint_info = (dec_attr.upper(), route_path)
            elif isinstance(d, ast.Name):
                decorators.append(d.id)
            elif isinstance(d, ast.Attribute):
                decorators.append(d.attr)

        params = [arg.arg for arg in node.args.args]
        docstring = ast.get_docstring(node)

        name = f"{parent_class}.{node.name}" if parent_class else node.name

        if endpoint_info:
            symbol_type = "endpoint"
            signature = f"@{endpoint_info[0]}('{endpoint_info[1]}') def {node.name}({', '.join(params)})"
        else:
            symbol_type = "function"
            signature = f"def {node.name}({', '.join(params)})"

        end_line = getattr(node, "end_lineno", node.lineno)

        return ParsedSymbol(
            name=name,
            symbol_type=symbol_type,
            start_line=node.lineno,
            end_line=end_line,
            signature=signature,
            parameters=params,
            docstring=docstring,
            metadata={
                "decorators": decorators,
                "parent_class": parent_class,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "func_name": node.name,
            },
        )

    def _parse_class(self, node: ast.ClassDef, code: str) -> ParsedSymbol:
        docstring = ast.get_docstring(node)
        bases = []
        for b in node.bases:
            if isinstance(b, ast.Name):
                bases.append(b.id)
            elif isinstance(b, ast.Attribute):
                bases.append(b.attr)

        decorators = []
        for d in node.decorator_list:
            if isinstance(d, ast.Name):
                decorators.append(d.id)
            elif isinstance(d, ast.Attribute):
                decorators.append(d.attr)

        # Detect Pydantic models or dataclasses
        is_model = any(b in ("BaseModel", "Model", "SQLModel", "Base") for b in bases) or "dataclass" in decorators
        symbol_type = "model" if is_model else "class"

        end_line = getattr(node, "end_lineno", node.lineno)

        return ParsedSymbol(
            name=node.name,
            symbol_type=symbol_type,
            start_line=node.lineno,
            end_line=end_line,
            signature=f"class {node.name}({', '.join(bases)})" if bases else f"class {node.name}",
            parameters=bases,
            docstring=docstring,
            metadata={"bases": bases, "decorators": decorators, "is_model": is_model},
        )
