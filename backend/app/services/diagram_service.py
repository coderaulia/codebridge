"""
CodeBridge V1 - Mermaid.js Visual Diagram Service
Generates validated Entity-Relationship (ER) diagrams and logic execution flowcharts.
"""
import re
from typing import List
from backend.app.parsers.base import ParsedSymbol, ParsedSchemaModel


class DiagramService:
    """Creates Mermaid.js markup for schemas and function execution journeys."""

    @staticmethod
    def generate_schema_er_diagram(models: List[ParsedSchemaModel]) -> str:
        """Generates a clean, validated Mermaid erDiagram block from schema models."""
        if not models:
            return ""

        lines = ["erDiagram"]
        seen_relationships = set()

        # 1. Output entities and their attributes
        for model in models:
            clean_name = re.sub(r"[^A-Za-z0-9_]", "_", model.model_name)
            lines.append(f"    {clean_name} {{")

            for f in model.fields[:12]:  # Limit to 12 fields per table to maintain readability
                f_name = re.sub(r"[^A-Za-z0-9_]", "_", f.get("name", "field"))
                f_type = re.sub(r"[^A-Za-z0-9_]", "_", f.get("type", "string"))
                pk_fk = ""
                if f.get("is_primary"):
                    pk_fk = "PK"
                elif f.get("is_foreign_key") or f.get("references_table"):
                    pk_fk = "FK"

                lines.append(f"        {f_type} {f_name} {pk_fk}".strip())

            lines.append("    }")

        # 2. Output relationships
        for model in models:
            from_name = re.sub(r"[^A-Za-z0-9_]", "_", model.model_name)
            for rel in model.relations:
                to_model = rel.get("to_model")
                if not to_model:
                    continue
                to_name = re.sub(r"[^A-Za-z0-9_]", "_", to_model)
                rel_key = tuple(sorted([from_name, to_name]))
                if rel_key in seen_relationships:
                    continue
                seen_relationships.add(rel_key)

                is_list = rel.get("is_list", False)
                cardinality = "}o--||" if is_list else "||--o|"
                label = rel.get("field", "relates_to")
                clean_label = re.sub(r"[^A-Za-z0-9_]", "_", label)
                lines.append(f"    {from_name} {cardinality} {to_name} : \"{clean_label}\"")

        return "\n".join(lines)

    @staticmethod
    def generate_flowchart_from_symbols(symbol: ParsedSymbol, steps: List[str] = None) -> str:
        """Generates a flowchart TD tracing input parameters, core logic, and return value."""
        lines = ["flowchart TD"]
        clean_func_name = re.sub(r"[^A-Za-z0-9_]", "_", symbol.name)

        # Start Node
        lines.append(f"    Start([\"Invoke: {symbol.name}\"])")

        # Inputs node
        if symbol.parameters:
            param_list = ", ".join(symbol.parameters[:4])
            lines.append(f"    Inputs[\"Inputs: {param_list}\"]")
            lines.append("    Start --> Inputs")
            prev_node = "Inputs"
        else:
            prev_node = "Start"

        # Steps / processing nodes
        if steps:
            for idx, step in enumerate(steps[:4]):
                step_node = f"Step_{idx+1}"
                clean_step = re.sub(r"[\"']", "", step)[:40]
                lines.append(f"    {step_node}[\"{clean_step}\"]")
                lines.append(f"    {prev_node} --> {step_node}")
                prev_node = step_node
        else:
            proc_node = f"Proc_{clean_func_name}"
            lines.append(f"    {proc_node}[\"Execute business logic in {symbol.name}\"]")
            lines.append(f"    {prev_node} --> {proc_node}")
            prev_node = proc_node

        # End node
        lines.append(f"    Done([\"Return Result / Complete Operation\"])")
        lines.append(f"    {prev_node} --> Done")

        return "\n".join(lines)
