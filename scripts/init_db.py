#!/usr/bin/env python3
"""One-time database schema initializer.

Usage: python scripts/init_db.py [--data-dir data]
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from research_tool.infrastructure.db.connection import apply_schema


async def main(data_dir: str) -> None:
    db_path = Path(data_dir) / "db.sqlite3"
    print(f"Initializing database at {db_path} ...")
    await apply_schema(db_path)
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()
    asyncio.run(main(args.data_dir))
