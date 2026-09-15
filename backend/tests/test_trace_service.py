"""
Unit tests for Cross-File Dataflow & Journey Tracing Engine
"""
import pytest
from backend.app.services.trace_service import TraceService, TraceHop


def test_build_sequence_diagram():
    hops = [
        TraceHop(
            target_file_id="f2",
            target_path="src/services/stripe.ts",
            target_domain="Financial & Payment Processing",
            target_language="typescript",
            referenced_symbols=["chargeCustomer"],
            relationship_type="service",
        ),
        TraceHop(
            target_file_id="f3",
            target_path="prisma/schema.prisma",
            target_domain="Data Persistence & Schemas",
            target_language="prisma",
            referenced_symbols=["Order"],
            relationship_type="database",
        ),
    ]

    seq = TraceService._build_sequence_diagram(
        origin_path="src/controllers/orderController.ts",
        origin_domain="API & External Communication",
        hops=hops,
    )

    assert "sequenceDiagram" in seq
    assert "orderController.ts" in seq
    assert "stripe.ts" in seq
    assert "schema.prisma" in seq
    assert "chargeCustomer" in seq
    assert "Order" in seq
