#!/usr/bin/env python3
"""
ARES Database Reset Script
==========================
Truncates ALL assessment data (projects, assessments, findings, evidence,
reports, activity_logs) and re-seeds one clean default project.

Usage (from backend/ directory):
    python scripts/reset_db.py

WARNING: This is DESTRUCTIVE and irreversible. All historical data is deleted.
"""

import asyncio
import sys
import os

# Ensure app package is importable when run from backend/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database.engine import init_db, AsyncSessionLocal
from app.models.models import Project


async def reset():
    print("=" * 60)
    print("ARES — Database Reset")
    print("=" * 60)

    # Initialise DB (creates tables if missing, does not seed)
    await init_db()

    async with AsyncSessionLocal() as db:
        # ── Count before ─────────────────────────────────────────
        def count(q):
            return asyncio.get_event_loop().run_until_complete  # unused helper below

        tables = ["activity_logs", "evidence", "reports", "findings", "assessments", "projects"]
        before = {}
        for t in tables:
            row = await db.execute(text(f"SELECT COUNT(*) FROM {t}"))
            before[t] = row.scalar()

        print("\nRecords BEFORE reset:")
        for t, n in before.items():
            print(f"  {t:<20} {n:>6}")

        # ── Delete in FK-safe order ───────────────────────────────
        print("\nDeleting all records …")
        for t in tables:
            await db.execute(text(f"DELETE FROM {t}"))
        await db.commit()

        # ── Seed one clean default project ────────────────────────
        print("Seeding default project …")
        db.add(Project(
            name="ARES Workspace",
            description="Default security assessment workspace",
        ))
        await db.commit()

        # ── Count after ──────────────────────────────────────────
        after = {}
        for t in tables:
            row = await db.execute(text(f"SELECT COUNT(*) FROM {t}"))
            after[t] = row.scalar()

        print("\nRecords AFTER reset:")
        for t, n in after.items():
            print(f"  {t:<20} {n:>6}")

    print("\n✓ Database reset complete. ARES is ready for a clean demo.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(reset())
