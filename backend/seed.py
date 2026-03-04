"""
PromptRank — Database Seeder

Loads predefined practice problems and their hidden testcases from
seed_data/problems.json into the database. Safe to run multiple times —
it skips problems that already exist (matched by title).

Usage:
    python seed.py
"""

import asyncio
import json
import os

from app.database import AsyncSessionLocal
from app.models import Problem, Testcase
from sqlalchemy import select


SEED_FILE = os.path.join(os.path.dirname(__file__), "seed_data", "problems.json")


async def seed():
    with open(SEED_FILE, "r", encoding="utf-8") as f:
        problems_data = json.load(f)

    async with AsyncSessionLocal() as db:
        inserted = 0
        skipped = 0

        for p in problems_data:
            # Check if problem already exists by title
            exists = await db.execute(
                select(Problem).where(Problem.title == p["title"])
            )
            if exists.scalar_one_or_none():
                skipped += 1
                continue

            # Create the problem
            problem = Problem(
                title=p["title"],
                statement=p["statement"],
                difficulty=p.get("difficulty", "medium"),
                time_limit_sec=p.get("time_limit_sec", 30),
                is_practice=True,
                contest_id=None,
            )
            db.add(problem)
            await db.flush()  # Get the problem.id

            # Create testcases
            for tc in p.get("testcases", []):
                testcase = Testcase(
                    problem_id=problem.id,
                    input_blob=tc["input_blob"],
                    expected_output_blob=tc["expected_output_blob"],
                    is_adversarial=tc.get("is_adversarial", False),
                )
                db.add(testcase)

            inserted += 1

        await db.commit()

    print(f"Seeding complete: {inserted} problems inserted, {skipped} skipped (already exist).")


if __name__ == "__main__":
    asyncio.run(seed())
