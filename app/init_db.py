"""Usage: python -m app.init_db [--reset] [--db PATH] [--no-seed]"""
import argparse
import os
import sys
from .seed import init_database

DEFAULT_DB = os.environ.get(
    "SHOPEASE_DATABASE",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "instance", "shopease.db"),
)


def main():
    parser = argparse.ArgumentParser(description="Initialise the local ShopEase test database.")
    parser.add_argument("--db", default=DEFAULT_DB, help="database path (default: instance/shopease.db)")
    parser.add_argument("--reset", action="store_true", help="delete the existing database file first")
    parser.add_argument("--no-seed", action="store_true", help="create empty tables only")
    args = parser.parse_args()
    if os.path.exists(args.db):
        if not args.reset:
            sys.exit(f"{args.db} already exists. Re-run with --reset to delete and recreate it.")
        os.remove(args.db)
    init_database(args.db, hash_method=os.environ.get("SHOPEASE_HASH_METHOD", "scrypt"), seed=not args.no_seed)
    print(f"Created {args.db} ({'empty' if args.no_seed else 'seeded with fictional test data'}).")


if __name__ == "__main__":
    main()
