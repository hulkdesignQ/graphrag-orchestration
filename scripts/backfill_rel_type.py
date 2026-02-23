#!/usr/bin/env python3
"""
Backfill rel_type property on existing RELATED_TO edges.

The persistence fix in a86ab57 now writes r.rel_type on every new RELATED_TO
edge, sourced from r.description (which has always stored the semantic type
string: "PARTY_TO", "LOCATED_IN", "DEFINES", etc.).

This script stamps rel_type on pre-existing edges where it is still NULL.
Safe to run multiple times — only touches edges where rel_type IS NULL.

Usage:
    python scripts/backfill_rel_type.py --group-id test-5pdfs-v2-fix2
    python scripts/backfill_rel_type.py --all-groups
    python scripts/backfill_rel_type.py --group-id test-5pdfs-v2-fix2 --verify
"""

import argparse
import os
import sys

from neo4j import GraphDatabase


def backfill(driver, group_id: str) -> int:
    cypher = """
    MATCH (e1:Entity {group_id: $group_id})-[r:RELATED_TO]->(e2:Entity {group_id: $group_id})
    WHERE r.rel_type IS NULL
    SET r.rel_type = coalesce(r.description, 'RELATED_TO')
    RETURN count(r) AS updated
    """
    with driver.session(database="neo4j") as session:
        result = session.run(cypher, group_id=group_id)
        record = result.single()
        return record["updated"] if record else 0


def verify(driver, group_id: str) -> None:
    """Print rel_type distribution and sample PARTY_TO edges."""
    dist_cypher = """
    MATCH (e1:Entity {group_id: $group_id})-[r:RELATED_TO]->(e2:Entity {group_id: $group_id})
    RETURN coalesce(r.rel_type, 'NULL') AS rel_type, count(r) AS cnt
    ORDER BY cnt DESC
    """
    sample_cypher = """
    MATCH (e1:Entity {group_id: $group_id})-[r:RELATED_TO {rel_type: 'PARTY_TO'}]->(e2:Entity {group_id: $group_id})
    RETURN e1.name AS subject, r.rel_type AS rel_type, e2.name AS object
    LIMIT 20
    """
    with driver.session(database="neo4j") as session:
        print("\n-- rel_type distribution --")
        for rec in session.run(dist_cypher, group_id=group_id):
            print(f"  {rec['rel_type']:30s}  {rec['cnt']}")

        print("\n-- sample PARTY_TO edges --")
        rows = list(session.run(sample_cypher, group_id=group_id))
        if rows:
            for rec in rows:
                print(f"  {rec['subject']}  ->  {rec['rel_type']}  ->  {rec['object']}")
        else:
            print("  (none found — LLM may not have extracted PARTY_TO for this group)")


def get_all_groups(driver) -> list:
    with driver.session(database="neo4j") as session:
        result = session.run(
            "MATCH (e:Entity) RETURN DISTINCT e.group_id AS g ORDER BY g"
        )
        return [r["g"] for r in result if r["g"]]


def main():
    parser = argparse.ArgumentParser(description="Backfill rel_type on RELATED_TO edges")
    parser.add_argument("--group-id", help="Specific group to backfill")
    parser.add_argument("--all-groups", action="store_true")
    parser.add_argument("--verify", action="store_true", help="Print distribution after backfill")
    args = parser.parse_args()

    if not args.group_id and not args.all_groups:
        parser.error("Must specify --group-id or --all-groups")

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_password = os.getenv("NEO4J_PASSWORD")

    if not neo4j_uri or not neo4j_password:
        print("NEO4J_URI and NEO4J_PASSWORD must be set")
        sys.exit(1)

    driver = GraphDatabase.driver(neo4j_uri, auth=("neo4j", neo4j_password))

    try:
        groups = get_all_groups(driver) if args.all_groups else [args.group_id]
        print(f"Processing {len(groups)} group(s): {groups}")

        for gid in groups:
            updated = backfill(driver, gid)
            print(f"  {gid}: stamped {updated} edges")
            if args.verify:
                verify(driver, gid)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
