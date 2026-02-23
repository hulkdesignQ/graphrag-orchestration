#!/usr/bin/env python3
"""Local test for Route 2 — all Q-L + Q-N questions.

Calls the Route 2 pipeline directly against live Neo4j + Azure OpenAI,
mirroring the same initialization as the API's _get_or_create_pipeline().
"""
import asyncio
import os
import sys
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Environment setup ──────────────────────────────────────────────
os.environ.setdefault("NEO4J_URI", "neo4j+s://a86dcf63.databases.neo4j.io")
os.environ.setdefault("NEO4J_USERNAME", "neo4j")
os.environ.setdefault("AZURE_OPENAI_ENDPOINT", "https://graphrag-openai-8476.openai.azure.com/")
os.environ.setdefault("AZURE_OPENAI_API_VERSION", "2024-10-21")
os.environ.setdefault("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4.1-mini")

# Load secrets from graphrag-orchestration/.env
_env_file = os.path.join(os.path.dirname(__file__), "graphrag-orchestration", ".env")
if os.path.exists(_env_file):
    import re as _re
    with open(_env_file) as _f:
        for _m in _re.finditer(r'^([A-Za-z_][A-Za-z0-9_]*)=(.+)', _f.read(), _re.MULTILINE):
            k, v = _m.groups()
            v = v.strip().strip('"')
            if k not in os.environ:
                os.environ[k] = v

# Ensure API key is set
if "AZURE_OPENAI_API_KEY" not in os.environ:
    import subprocess
    try:
        key = subprocess.check_output(
            ["az", "cognitiveservices", "account", "keys", "list",
             "--name", "graphrag-openai-8476",
             "--resource-group", "rg-graphrag-feature",
             "--query", "key1", "-o", "tsv"],
            text=True, timeout=15
        ).strip()
        os.environ["AZURE_OPENAI_API_KEY"] = key
    except Exception as e:
        print(f"WARNING: Could not get Azure OpenAI key: {e}")

from src.core.config import settings

# ── Test questions ─────────────────────────────────────────────────
QUESTIONS = [
    # Positive (Q-L): Route 2 should find the answer
    {"qid": "Q-L1", "question": "Who is the Agent in the property management agreement?", "expected": "Walt Flood Realty", "negative": False},
    {"qid": "Q-L2", "question": "Who is the Owner in the property management agreement?", "expected": "Contoso Ltd.", "negative": False},
    {"qid": "Q-L3", "question": "What is the managed property address in the property management agreement?", "expected": "456 Palm Tree Avenue, Honolulu, HI 96815", "negative": False},
    {"qid": "Q-L4", "question": "What is the initial term start date in the property management agreement?", "expected": "2010-06-15", "negative": False},
    {"qid": "Q-L5", "question": "What written notice period is required for termination of the property management agreement?", "expected": "sixty (60) days written notice", "negative": False},
    {"qid": "Q-L6", "question": "What is the Agent fee/commission for short-term rentals (less than 180 days)?", "expected": "twenty five percent (25%) of the gross revenues", "negative": False},
    {"qid": "Q-L7", "question": "What is the Agent fee/commission for long-term leases (more than 180 days)?", "expected": "ten percent (10%) of the gross revenues", "negative": False},
    {"qid": "Q-L8", "question": "What is the pro-ration advertising charge and minimum admin/accounting charge in the property management agreement?", "expected": "$75.00/month advertising; $50.00/month minimum admin/accounting", "negative": False},
    {"qid": "Q-L9", "question": "In the purchase contract Exhibit A, what is the job location?", "expected": "811 Ocean Drive, Suite 405, Tampa, FL 33602", "negative": False},
    {"qid": "Q-L10", "question": "In the purchase contract Exhibit A, what is the contact's name and email?", "expected": "Elizabeth Nolasco; enolasco@fabrikam.com", "negative": False},
    # Negative (Q-N): Route 2 should refuse
    {"qid": "Q-N1", "question": "What is the invoice's bank routing number for payment?", "expected": "Not specified", "negative": True},
    {"qid": "Q-N2", "question": "What is the invoice's IBAN / SWIFT (BIC) for international payments?", "expected": "Not specified", "negative": True},
    {"qid": "Q-N3", "question": "What is the vendor's VAT / Tax ID number on the invoice?", "expected": "Not specified", "negative": True},
    {"qid": "Q-N5", "question": "What is the invoice's bank account number for ACH/wire payments?", "expected": "Not specified", "negative": True},
    {"qid": "Q-N6", "question": "Which documents are governed by the laws of California?", "expected": "None", "negative": True},
    {"qid": "Q-N7", "question": "What is the property management Agent's license number?", "expected": "Not specified", "negative": True},
    {"qid": "Q-N8", "question": "What is the purchase contract's required wire transfer / ACH instructions?", "expected": "Not specified", "negative": True},
    {"qid": "Q-N9", "question": "What is the exact clause about mold damage coverage in the warranty?", "expected": "Not specified", "negative": True},
    {"qid": "Q-N10", "question": "What is the invoice shipping method (value in SHIPPED VIA)?", "expected": "Not specified", "negative": True},
]

GROUP_ID = os.getenv("TEST_GROUP_ID", "test-5pdfs-v2-fix2")

_pipeline = None


async def get_pipeline():
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    from src.worker.hybrid_v2.orchestrator import HybridPipeline
    from src.worker.hybrid_v2.router.main import DeploymentProfile
    from src.worker.services import GraphService, LLMService
    from src.worker.hybrid_v2.indexing.text_store import Neo4jTextUnitStore
    from src.worker.services.async_neo4j_service import AsyncNeo4jService

    llm_service = LLMService()
    llm_client = llm_service.get_synthesis_llm()

    graph_service = GraphService()
    graph_store = graph_service.get_store(GROUP_ID)
    neo4j_driver = graph_service.driver

    text_unit_store = Neo4jTextUnitStore(neo4j_driver, group_id=GROUP_ID)

    embedding_client = llm_service.embed_model
    if settings.VOYAGE_API_KEY:
        async_service = AsyncNeo4jService(
            uri=settings.NEO4J_URI,
            username=settings.NEO4J_USERNAME,
            password=settings.NEO4J_PASSWORD,
        )
        await async_service.connect()
        embedding_version = await async_service.detect_embedding_version(GROUP_ID)
        await async_service.close()
        if embedding_version == "v2":
            from src.worker.hybrid_v2.embeddings.voyage_embed import VoyageEmbedService
            voyage_service = VoyageEmbedService()
            embedding_client = voyage_service.get_llama_index_embed_model()
            print(f"  Embeddings: Voyage v2")
        else:
            print(f"  Embeddings: OpenAI v1")

    hipporag_instance = None
    skip_hipporag = os.getenv("SKIP_HIPPORAG", "0") == "1"
    if skip_hipporag:
        print(f"  HippoRAG: SKIPPED (SKIP_HIPPORAG=1) — using Cypher PPR path")
    else:
        try:
            from src.worker.hybrid.indexing.hipporag_service import get_hipporag_service
            hipporag_service = get_hipporag_service(GROUP_ID, "./hipporag_index")
            await hipporag_service.initialize()
            hipporag_instance = hipporag_service.get_instance()
            print(f"  HippoRAG: initialized")
        except Exception as e:
            print(f"  HippoRAG: unavailable ({type(e).__name__})")

    _pipeline = HybridPipeline(
        profile=DeploymentProfile.GENERAL_ENTERPRISE,
        llm_client=llm_client,
        embedding_client=embedding_client,
        hipporag_instance=hipporag_instance,
        graph_store=graph_store,
        neo4j_driver=neo4j_driver,
        text_unit_store=text_unit_store,
        group_id=GROUP_ID,
    )
    await _pipeline.initialize()
    return _pipeline


async def run_route2(query: str) -> dict:
    from src.worker.hybrid_v2.router.main import QueryRoute
    pipeline = await get_pipeline()
    result = await pipeline.force_route(
        query=query,
        route=QueryRoute.LOCAL_SEARCH,
        response_type="summary",
    )
    return result.to_dict() if hasattr(result, 'to_dict') else result


async def main():
    print("=" * 70)
    print("Route 2 Local Test — Full Question Bank")
    print("=" * 70)
    print(f"Group ID: {GROUP_ID}")
    print(f"Skeleton: enabled={settings.SKELETON_ENRICHMENT_ENABLED}, model={settings.SKELETON_SYNTHESIS_MODEL}")
    print()

    passes = 0
    fails = 0
    errors = 0
    results_table = []

    # Filter by CLI arg if provided
    filter_qid = sys.argv[1] if len(sys.argv) > 1 else None
    questions = QUESTIONS
    if filter_qid:
        questions = [q for q in QUESTIONS if filter_qid.upper() in q["qid"].upper()]
        if not questions:
            print(f"No questions matching '{filter_qid}'")
            return

    for q in questions:
        print(f"\n--- {q['qid']}: {q['question'][:55]}... ---")
        t0 = time.perf_counter()
        try:
            result = await run_route2(q["question"])
            elapsed = time.perf_counter() - t0

            response = result.get("response", "") if isinstance(result, dict) else str(result)
            resp_lower = response.lower()
            not_found = "not found" in resp_lower or "not specified" in resp_lower

            if q["negative"]:
                # Negative test: should refuse
                if not_found:
                    status = "PASS"
                    passes += 1
                else:
                    status = "FAIL (should refuse)"
                    fails += 1
            else:
                # Positive test: should find answer
                if not_found:
                    status = "FAIL (refusal)"
                    fails += 1
                else:
                    status = "PASS"
                    passes += 1

            print(f"  {status} ({elapsed:.1f}s)")
            print(f"  Response: {response[:200]}")
            if not q["negative"]:
                print(f"  Expected: {q['expected']}")

            meta = result.get("metadata", {}) if isinstance(result, dict) else {}
            cs = meta.get("context_stats", {})
            ds = cs.get("retrieval", {}).get("doc_scope", {})
            print(f"  doc_scope: {ds.get('decision', 'N/A')}")

            results_table.append({"qid": q["qid"], "status": status, "time": f"{elapsed:.1f}s"})

        except Exception as e:
            elapsed = time.perf_counter() - t0
            print(f"  ERROR ({elapsed:.1f}s): {e}")
            errors += 1
            results_table.append({"qid": q["qid"], "status": f"ERROR: {e}", "time": f"{elapsed:.1f}s"})

    print("\n" + "=" * 70)
    print(f"RESULTS: {passes} pass, {fails} fail, {errors} errors / {len(questions)} total")
    print("=" * 70)
    for r in results_table:
        mark = "✓" if "PASS" in r["status"] else "✗" if "FAIL" in r["status"] else "!"
        print(f"  {mark} {r['qid']:6s} {r['status']:25s} {r['time']}")


if __name__ == "__main__":
    asyncio.run(main())
