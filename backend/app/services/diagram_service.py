"""
CodeBridge V1 - Mermaid.js Visual Diagram Service
Generates validated Entity-Relationship (ER) diagrams and logic execution flowcharts.
"""
import re
from typing import List, Dict, Any, Optional
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

    @staticmethod
    def generate_macro_architecture_diagram(domains_data: List[Dict[str, Any]]) -> str:
        """Generates an executive-level multi-tier system architecture diagram from business domains."""
        if not domains_data:
            return ""

        tier_ui = []
        tier_api = []
        tier_services = []
        tier_data = []
        tier_infra = []

        for d in domains_data:
            name = d.get("domain_name", "")
            lowered = name.lower()
            count = d.get("file_count", 0)
            sample = d.get("sample_files", "")
            node_id = re.sub(r"[^A-Za-z0-9_]", "_", name)
            item = {"id": node_id, "name": name, "count": count, "sample": sample}

            if any(k in lowered for k in ("ui", "user interface", "frontend", "client", "view")):
                tier_ui.append(item)
            elif any(k in lowered for k in ("api", "route", "gateway", "external communication", "endpoint")):
                tier_api.append(item)
            elif any(k in lowered for k in ("data persistence", "schema", "database", "model", "migration", "prisma", "sql")):
                tier_data.append(item)
            elif any(k in lowered for k in ("analytics", "observability", "telemetry", "metric", "logging")):
                tier_infra.append(item)
            else:
                tier_services.append(item)

        lines = ["flowchart TD"]

        def render_tier(subgraph_id: str, label: str, items: List[Dict[str, Any]]):
            if not items:
                return
            lines.append(f"    subgraph {subgraph_id} [\"{label}\"]")
            for item in items:
                lines.append(f"        {item['id']}[\"{item['name']}<br/><i>({item['count']} files)</i>\"]")
            lines.append("    end")

        render_tier("UI_Layer", "🖥️ Presentation & Client Tier", tier_ui)
        render_tier("API_Layer", "🌐 API Gateway & Route Handlers", tier_api)
        render_tier("Service_Layer", "⚙️ Core Business Domain Services", tier_services)
        render_tier("Data_Layer", "🗄️ Data Persistence & Schemas", tier_data)
        render_tier("Infra_Layer", "📊 Observability & Infrastructure", tier_infra)

        # Cross-tier directional connections
        if tier_ui and tier_api:
            for u in tier_ui:
                for a in tier_api:
                    lines.append(f"    {u['id']} -->|HTTP / JSON| {a['id']}")
        elif tier_ui and tier_services:
            for u in tier_ui:
                for s in tier_services[:2]:
                    lines.append(f"    {u['id']} --> {s['id']}")

        if tier_api and tier_services:
            for a in tier_api:
                for s in tier_services:
                    lines.append(f"    {a['id']} --> {s['id']}")
        elif tier_api and tier_data:
            for a in tier_api:
                for d in tier_data:
                    lines.append(f"    {a['id']} -->|Queries| {d['id']}")

        if tier_services and tier_data:
            for s in tier_services:
                for d in tier_data:
                    lines.append(f"    {s['id']} -->|Read / Write| {d['id']}")

        if tier_infra:
            inf = tier_infra[0]
            if tier_services:
                lines.append(f"    {tier_services[0]['id']} -.->|Metrics| {inf['id']}")
            elif tier_api:
                lines.append(f"    {tier_api[0]['id']} -.->|Logs| {inf['id']}")

        # Styling
        lines.append("    classDef ui fill:#1e1b4b,stroke:#6366f1,stroke-width:1.5px,color:#e0e7ff")
        lines.append("    classDef api fill:#14293a,stroke:#06b6d4,stroke-width:1.5px,color:#cffafe")
        lines.append("    classDef svc fill:#2e1065,stroke:#a855f7,stroke-width:1.5px,color:#f3e8ff")
        lines.append("    classDef data fill:#064e3b,stroke:#10b981,stroke-width:1.5px,color:#d1fae5")
        lines.append("    classDef infra fill:#3f2c06,stroke:#f59e0b,stroke-width:1.5px,color:#fef3c7")

        for u in tier_ui:
            lines.append(f"    class {u['id']} ui")
        for a in tier_api:
            lines.append(f"    class {a['id']} api")
        for s in tier_services:
            lines.append(f"    class {s['id']} svc")
        for d in tier_data:
            lines.append(f"    class {d['id']} data")
        for i in tier_infra:
            lines.append(f"    class {i['id']} infra")

        return "\n".join(lines)
