"""
Folder Resolver Service

Resolves folder_id → root_folder_id for use as Neo4j partition key (group_id).

Architecture:
- auth_group_id (B2B group / B2C user_id) = security boundary
- root_folder_id = Neo4j partition key (one knowledge graph per root folder)
- Unfiled documents (folder_id=None) fall back to auth_group_id
"""

import logging
from typing import Optional
import structlog

logger = logging.getLogger(__name__)
slogger = structlog.get_logger(__name__)


async def resolve_neo4j_group_id(
    auth_group_id: str,
    folder_id: Optional[str] = None,
) -> str:
    """Resolve the Neo4j partition key from folder context.

    Args:
        auth_group_id: The authenticated user/group identity (security boundary).
        folder_id: Optional folder ID (root or subfolder). If a subfolder,
                   walks SUBFOLDER_OF edges to find the root folder.

    Returns:
        The root_folder_id to use as Neo4j group_id, or auth_group_id if
        no folder context is provided.

    Raises:
        ValueError: If the folder doesn't exist or doesn't belong to auth_group_id.
    """
    import os
    from src.core.config import settings

    # Read DEMO_GROUP_ID with env-var fallback.  Pydantic BaseSettings is
    # mutable (not frozen) and the singleton value can drift from the real
    # environment variable in long-running processes.
    demo_group_id = settings.DEMO_GROUP_ID or os.environ.get("DEMO_GROUP_ID") or None

    if folder_id == "__demo__":
        if demo_group_id:
            slogger.info("demo_folder_resolved", result=demo_group_id)
            return demo_group_id
        slogger.warning("demo_folder_no_demo_group_id", falling_back_to=auth_group_id)
        return auth_group_id

    if not folder_id:
        # No folder selected — use DEMO_GROUP_ID if configured,
        # otherwise fall back to first user root folder partition.

        if demo_group_id:
            slogger.info("no_folder_using_demo_group", demo_group=demo_group_id)
            return demo_group_id

        partition_ids = await _get_user_root_folder_ids(auth_group_id)
        if partition_ids:
            logger.info(
                "no_folder_selected_using_first_partition",
                extra={"auth_group_id": auth_group_id, "partition": partition_ids[0]},
            )
            return partition_ids[0]
        return auth_group_id

    from src.worker.services import GraphService

    driver = GraphService().driver
    if not driver:
        raise ValueError("Neo4j driver not initialized")

    with driver.session() as session:
        # Walk SUBFOLDER_OF to root and verify ownership
        result = session.run(
            """
            MATCH (f:Folder {id: $folder_id, group_id: $auth_gid})
            OPTIONAL MATCH (f)-[:SUBFOLDER_OF*1..]->(root:Folder)
            WHERE NOT (root)-[:SUBFOLDER_OF]->(:Folder)
            WITH f, root
            RETURN COALESCE(root.id, f.id) AS root_folder_id
            """,
            folder_id=folder_id,
            auth_gid=auth_group_id,
        )
        record = result.single()

        if not record:
            raise ValueError(
                f"Folder '{folder_id}' not found or does not belong to group '{auth_group_id}'"
            )

        root_id = record["root_folder_id"]
        logger.info(
            "folder_resolved_to_neo4j_group",
            extra={
                "auth_group_id": auth_group_id,
                "folder_id": folder_id,
                "root_folder_id": root_id,
            },
        )
        return root_id


async def _get_user_root_folder_ids(auth_group_id: str) -> list:
    """Get root user-folder IDs for a given auth_group_id.

    Only returns folder_type='user' roots that have been analyzed,
    skipping 'analysis_result' container folders which have no indexed data.
    """
    from src.worker.services import GraphService

    driver = GraphService().driver
    if not driver:
        return []

    with driver.session() as session:
        result = session.run(
            """
            MATCH (f:Folder {group_id: $auth_gid, folder_type: 'user'})
            WHERE f.parent_folder_id IS NULL
              AND f.analysis_status IN ['analyzed', 'stale']
            RETURN f.id AS root_folder_id
            ORDER BY f.name
            """,
            auth_gid=auth_group_id,
        )
        return [r["root_folder_id"] for r in result]


async def get_valid_partition_ids(auth_group_id: str) -> list:
    """Get all valid Neo4j partition IDs for a given auth_group_id.

    Returns auth_group_id (for unfiled docs) plus all root folder IDs.
    """
    from src.worker.services import GraphService

    driver = GraphService().driver
    if not driver:
        return [auth_group_id]

    with driver.session() as session:
        result = session.run(
            """
            MATCH (f:Folder {group_id: $auth_gid})
            WHERE NOT (f)-[:SUBFOLDER_OF]->(:Folder)
            RETURN f.id AS root_folder_id
            """,
            auth_gid=auth_group_id,
        )
        root_ids = [r["root_folder_id"] for r in result]

    return [auth_group_id] + root_ids
