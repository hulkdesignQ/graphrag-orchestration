"""Tests for the folder file-count endpoint."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api_gateway.routers.folders import router, get_partition_id


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

GRAPH_SERVICE_PATH = "src.api_gateway.routers.folders.GraphService"
RESOLVE_PATH = "src.api_gateway.routers.files._resolve_folder_path"


def _build_app(blob_manager=None) -> FastAPI:
    """Create a minimal FastAPI app with the folders router and mocked deps."""
    app = FastAPI()
    app.include_router(router)
    if blob_manager is not None:
        app.state.user_blob_manager = blob_manager
    return app


def _mock_neo4j_session(records_by_query: dict[str, list]):
    """Create a mock Neo4j session that returns different results per query.
    
    records_by_query maps a keyword found in the Cypher query to the
    list of mock records to return (or None for single()).
    """
    mock_session = MagicMock()

    def side_effect(query, **kwargs):
        result = MagicMock()
        for keyword, value in records_by_query.items():
            if keyword in query:
                if isinstance(value, dict):
                    # single() returns a record
                    rec = MagicMock()
                    rec.__getitem__ = lambda self, key, v=value: v.get(key)
                    rec.get = lambda key, default=None, v=value: v.get(key, default)
                    result.single.return_value = rec
                elif isinstance(value, list):
                    # iteration returns list of records
                    recs = []
                    for item in value:
                        r = MagicMock()
                        r.__getitem__ = lambda self, key, v=item: v.get(key)
                        recs.append(r)
                    result.__iter__ = lambda self, r=recs: iter(r)
                    result.single.return_value = recs[0] if recs else None
                elif value is None:
                    result.single.return_value = None
                return result
        # Default: empty result
        result.single.return_value = None
        result.__iter__ = lambda self: iter([])
        return result

    mock_session.run = side_effect
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    return mock_session


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@patch(RESOLVE_PATH, new_callable=AsyncMock)
@patch(GRAPH_SERVICE_PATH)
def test_file_count_single_folder(mock_graph_cls, mock_resolve):
    """Endpoint returns blob count for a leaf folder with no subfolders."""
    mock_driver = MagicMock()
    mock_driver.session.return_value = _mock_neo4j_session({
        "f.id AS id": {"id": "folder-123"},
        "folder_ids": {"folder_ids": ["folder-123"]},
    })
    mock_graph_cls.return_value.driver = mock_driver

    mock_resolve.return_value = "Contracts"

    blob_manager = MagicMock()
    blob_manager.list_blobs_recursive = AsyncMock(return_value=[
        {"name": "file1.pdf", "url": "u", "full_path": "g/Contracts/file1.pdf"},
        {"name": "file2.pdf", "url": "u", "full_path": "g/Contracts/file2.pdf"},
    ])

    app = _build_app(blob_manager)
    app.dependency_overrides[get_partition_id] = lambda: "test-group"

    client = TestClient(app)
    resp = client.get("/folders/folder-123/file-count")

    assert resp.status_code == 200
    body = resp.json()
    assert body["folder_id"] == "folder-123"
    assert body["count"] == 2


@patch(RESOLVE_PATH, new_callable=AsyncMock)
@patch(GRAPH_SERVICE_PATH)
def test_file_count_aggregates_across_subfolders(mock_graph_cls, mock_resolve):
    """Endpoint sums blob counts across parent + all descendant subfolders."""
    mock_driver = MagicMock()
    mock_driver.session.return_value = _mock_neo4j_session({
        "f.id AS id": {"id": "parent-id"},
        "folder_ids": {"folder_ids": ["parent-id", "child-id", "grandchild-id"]},
    })
    mock_graph_cls.return_value.driver = mock_driver

    mock_resolve.side_effect = ["Parent", "Parent/Child", "Parent/Child/Grandchild"]

    blob_manager = MagicMock()
    blob_manager.list_blobs_recursive = AsyncMock(side_effect=[
        [{"name": "a.pdf", "url": "u", "full_path": "g/Parent/a.pdf"}],
        [{"name": "b.pdf", "url": "u", "full_path": "g/Parent/Child/b.pdf"},
         {"name": "c.pdf", "url": "u", "full_path": "g/Parent/Child/c.pdf"}],
        [],
    ])

    app = _build_app(blob_manager)
    app.dependency_overrides[get_partition_id] = lambda: "test-group"

    client = TestClient(app)
    resp = client.get("/folders/parent-id/file-count")

    assert resp.status_code == 200
    assert resp.json()["count"] == 3  # 1 + 2 + 0


@patch(RESOLVE_PATH, new_callable=AsyncMock)
@patch(GRAPH_SERVICE_PATH)
def test_file_count_parent_empty_subfolders_have_files(mock_graph_cls, mock_resolve):
    """The exact CTA bug scenario: parent has 0 files, children have files."""
    mock_driver = MagicMock()
    mock_driver.session.return_value = _mock_neo4j_session({
        "f.id AS id": {"id": "parent-id"},
        "folder_ids": {"folder_ids": ["parent-id", "input-id", "ref-id"]},
    })
    mock_graph_cls.return_value.driver = mock_driver

    mock_resolve.side_effect = [
        "insurance_claims_review",
        "insurance_claims_review/input_docs",
        "insurance_claims_review/reference_docs",
    ]

    blob_manager = MagicMock()
    blob_manager.list_blobs_recursive = AsyncMock(side_effect=[
        [],  # parent: 0
        [{"name": "claim1.pdf"}, {"name": "claim2.pdf"}],  # 2
        [{"name": "ref1.pdf"}, {"name": "ref2.pdf"}, {"name": "ref3.pdf"}, {"name": "ref4.pdf"}],  # 4
    ])

    app = _build_app(blob_manager)
    app.dependency_overrides[get_partition_id] = lambda: "test-group"

    client = TestClient(app)
    resp = client.get("/folders/parent-id/file-count")

    assert resp.status_code == 200
    assert resp.json()["count"] == 6  # 0 + 2 + 4 — CTA should show!


@patch(RESOLVE_PATH, new_callable=AsyncMock)
@patch(GRAPH_SERVICE_PATH)
def test_file_count_returns_zero_for_empty_tree(mock_graph_cls, mock_resolve):
    """Endpoint returns count=0 when folder and all subfolders have no blobs."""
    mock_driver = MagicMock()
    mock_driver.session.return_value = _mock_neo4j_session({
        "f.id AS id": {"id": "folder-empty"},
        "folder_ids": {"folder_ids": ["folder-empty"]},
    })
    mock_graph_cls.return_value.driver = mock_driver

    mock_resolve.return_value = "Empty"

    blob_manager = MagicMock()
    blob_manager.list_blobs_recursive = AsyncMock(return_value=[])

    app = _build_app(blob_manager)
    app.dependency_overrides[get_partition_id] = lambda: "test-group"

    client = TestClient(app)
    resp = client.get("/folders/folder-empty/file-count")

    assert resp.status_code == 200
    assert resp.json()["count"] == 0


@patch(GRAPH_SERVICE_PATH)
def test_file_count_404_when_folder_not_found(mock_graph_cls):
    """Endpoint returns 404 when folder doesn't exist in Neo4j."""
    mock_driver = MagicMock()
    mock_driver.session.return_value = _mock_neo4j_session({
        "f.id AS id": None,
    })
    mock_graph_cls.return_value.driver = mock_driver

    app = _build_app(MagicMock())
    app.dependency_overrides[get_partition_id] = lambda: "test-group"

    client = TestClient(app)
    resp = client.get("/folders/nonexistent/file-count")

    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


@patch(RESOLVE_PATH, new_callable=AsyncMock)
@patch(GRAPH_SERVICE_PATH)
def test_file_count_400_when_no_blob_manager(mock_graph_cls, mock_resolve):
    """Endpoint returns 400 when blob storage is not configured."""
    mock_driver = MagicMock()
    mock_driver.session.return_value = _mock_neo4j_session({
        "f.id AS id": {"id": "folder-123"},
        "folder_ids": {"folder_ids": ["folder-123"]},
    })
    mock_graph_cls.return_value.driver = mock_driver

    app = _build_app()  # no blob_manager
    app.dependency_overrides[get_partition_id] = lambda: "test-group"

    client = TestClient(app)
    resp = client.get("/folders/folder-123/file-count")

    assert resp.status_code == 400
    assert "not configured" in resp.json()["detail"].lower()
