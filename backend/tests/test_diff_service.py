"""
Unit tests for Git Diff & Pull Request Translation Service
"""
import pytest
from backend.app.services.diff_service import DiffService


def test_parse_diff_structure():
    sample_diff = """diff --git a/src/services/billing.ts b/src/services/billing.ts
index 1234567..89abcdef 100644
--- a/src/services/billing.ts
+++ b/src/services/billing.ts
@@ -10,4 +10,8 @@ export async function chargeCard() {
+    const idempotencyKey = uuidv4();
+    return stripe.charges.create({ idempotencyKey });
 }
diff --git a/prisma/schema.prisma b/prisma/schema.prisma
index 2345678..90abcdef 100644
--- a/prisma/schema.prisma
+++ b/prisma/schema.prisma
@@ -5,3 +5,4 @@ model Order {
+    idempotencyKey String?
"""
    changes = DiffService.parse_diff_structure(sample_diff)
    assert len(changes) == 2

    billing_change = next(c for c in changes if "billing.ts" in c.file_path)
    assert billing_change.lines_added == 2
    assert not billing_change.is_schema

    prisma_change = next(c for c in changes if "schema.prisma" in c.file_path)
    assert prisma_change.lines_added == 1
    assert prisma_change.is_schema


@pytest.mark.asyncio
async def test_translate_diff():
    sample_diff = """diff --git a/src/services/auth.ts b/src/services/auth.ts
--- a/src/services/auth.ts
+++ b/src/services/auth.ts
@@ -1,3 +1,4 @@
+export const JWT_SECRET = "production-secret";
"""
    service = DiffService()
    res = await service.translate_diff(sample_diff, project_name="TestApp")

    assert res.summary != ""
    assert res.user_impact != ""
    assert res.risk_level in ("LOW", "MEDIUM", "HIGH")
    assert len(res.files_changed) == 1
