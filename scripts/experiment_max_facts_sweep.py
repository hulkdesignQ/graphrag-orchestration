#!/usr/bin/env python3
"""Experiment: Sweep ROUTE7_RECOGNITION_MEMORY_MAX_FACTS from 4 to 8.

Tests the effect of increasing the recognition memory filter's max_facts
parameter on Q-D3 (the 1/57 gap — missing "3 business days" and "10 business days").

Runs the full benchmark for each max_facts value, first Q-D3 only, then
optionally full benchmark with the best value.

Usage:
    # After reindex + API server start:
    PYTHONPATH=. python3 scripts/experiment_max_facts_sweep.py \
        --url http://localhost:8000 --no-auth

    # Or against cloud:
    PYTHONPATH=. python3 scripts/experiment_max_facts_sweep.py
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ── Question bank (Q-D3 + full set) ────────────────────────────────
QD3_QUESTION = "Compare \"time windows\" across the set: list all explicit day-based timeframes."
QD3_EXPECTED_KEYWORDS = [
    "60 days", "60-day", "sixty",
    "5 business days", "five (5) business",
    "180 days",
    "90 days", "ninety",
    "3 business days", "three (3) business",      # currently missing
    "10 business days", "ten (10) business",       # currently missing
    "1 year", "one (1) year", "12 months",
]

CRITICAL_MISSING = [
    "3 business days",
    "10 business days",
]


def _http_post(url: str, payload: dict, headers: dict, timeout: float = 180) -> dict:
    """Simple HTTP POST using urllib (no deps)."""
    import urllib.request
    import urllib.error

    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"    ⚠️  HTTP {e.code}: {body[:200]}")
        return {"error": f"HTTP {e.code}", "detail": body}
    except Exception as e:
        print(f"    ⚠️  Error: {e}")
        return {"error": str(e)}


def _wait_for_api(url: str, max_wait: int = 60) -> bool:
    """Wait for API health endpoint."""
    import urllib.request
    import urllib.error

    health_url = f"{url.rstrip('/')}/health"
    for _ in range(max_wait):
        try:
            with urllib.request.urlopen(health_url, timeout=5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(1)
    return False


def run_qd3_with_max_facts(
    api_url: str,
    group_id: str,
    max_facts: int,
    repeats: int = 3,
    no_auth: bool = False,
    include_context: bool = True,
) -> Dict[str, Any]:
    """Run Q-D3 with a specific max_facts value."""
    url = f"{api_url.rstrip('/')}/hybrid/query"
    headers = {"Content-Type": "application/json", "X-Group-ID": group_id}

    if not no_auth:
        try:
            result = subprocess.run(
                ["az", "account", "get-access-token", "--resource", "https://management.azure.com/"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                token = json.loads(result.stdout).get("accessToken", "")
                if token:
                    headers["Authorization"] = f"Bearer {token}"
        except Exception:
            pass

    runs = []
    for rep in range(1, repeats + 1):
        payload = {
            "group_id": group_id,
            "query": QD3_QUESTION,
            "response_type": "summary",
            "force_route": "hipporag2_search",
        }
        if include_context:
            payload["include_context"] = True

        t0 = time.time()
        resp = _http_post(url, payload, headers)
        elapsed_ms = int((time.time() - t0) * 1000)

        answer = resp.get("response", "") or resp.get("answer", "")
        llm_context = (resp.get("metadata") or {}).get("llm_context", "")

        # Check keyword hits
        answer_lower = answer.lower()
        keyword_hits = [kw for kw in QD3_EXPECTED_KEYWORDS if kw.lower() in answer_lower]
        critical_hits = [kw for kw in CRITICAL_MISSING if kw.lower() in answer_lower]

        run_data = {
            "run": rep,
            "answer": answer[:1000],
            "elapsed_ms": elapsed_ms,
            "keyword_hits": keyword_hits,
            "keyword_count": len(keyword_hits),
            "critical_hits": critical_hits,
            "critical_count": len(critical_hits),
            "total_keywords": len(QD3_EXPECTED_KEYWORDS),
        }
        if llm_context:
            run_data["llm_context_length"] = len(str(llm_context))
            # Check if business days appear in context
            ctx_lower = str(llm_context).lower()
            run_data["context_has_3_business_days"] = "3 business day" in ctx_lower
            run_data["context_has_10_business_days"] = "10 business day" in ctx_lower

        runs.append(run_data)
        print(f"  [rep {rep}/{repeats}] {elapsed_ms}ms | keywords: {len(keyword_hits)}/{len(QD3_EXPECTED_KEYWORDS)} | critical: {len(critical_hits)}/{len(CRITICAL_MISSING)}")

    # Summary
    avg_keywords = sum(r["keyword_count"] for r in runs) / len(runs) if runs else 0
    avg_critical = sum(r["critical_count"] for r in runs) / len(runs) if runs else 0
    best_keywords = max(r["keyword_count"] for r in runs) if runs else 0
    best_critical = max(r["critical_count"] for r in runs) if runs else 0

    return {
        "max_facts": max_facts,
        "runs": runs,
        "avg_keyword_hits": round(avg_keywords, 1),
        "best_keyword_hits": best_keywords,
        "avg_critical_hits": round(avg_critical, 1),
        "best_critical_hits": best_critical,
    }


def start_api_server(max_facts: int, port: int = 8000) -> subprocess.Popen:
    """Start API server with specific max_facts env var."""
    # Kill any leftover process on this port
    try:
        result = subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True, text=True)
        if result.stdout.strip():
            for pid in result.stdout.strip().split('\n'):
                try:
                    os.kill(int(pid), signal.SIGKILL)
                except (ProcessLookupError, ValueError):
                    pass
            time.sleep(1)
    except Exception:
        pass

    env = os.environ.copy()
    env["ROUTE7_RECOGNITION_MEMORY_MAX_FACTS"] = str(max_facts)
    env["REQUIRE_AUTH"] = "false"
    env["ALLOW_LEGACY_GROUP_HEADER"] = "true"
    env["PYTHONPATH"] = "."

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.api_gateway.main:app",
         "--host", "0.0.0.0", "--port", str(port), "--log-level", "warning"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,
    )
    return proc


def stop_api_server(proc: subprocess.Popen):
    """Stop API server."""
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait(timeout=10)
    except Exception:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="Sweep ROUTE7_RECOGNITION_MEMORY_MAX_FACTS")
    parser.add_argument("--url", type=str, default=None,
                        help="API URL (if already running). Skips server lifecycle management.")
    parser.add_argument("--group-id", type=str, default=None)
    parser.add_argument("--no-auth", action="store_true", default=False)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--min-facts", type=int, default=4)
    parser.add_argument("--max-facts", type=int, default=8)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    # Resolve group ID
    group_id = args.group_id or os.getenv("TEST_GROUP_ID") or os.getenv("GROUP_ID")
    if not group_id:
        gid_file = Path("last_test_group_id.txt")
        if gid_file.exists():
            group_id = gid_file.read_text().strip()
    if not group_id:
        group_id = "test-5pdfs-v2-fix2"
    print(f"Group ID: {group_id}")

    external_api = args.url is not None
    api_url = args.url or f"http://localhost:{args.port}"

    ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    results = {
        "experiment": "recognition_memory_max_facts_sweep",
        "timestamp": ts,
        "group_id": group_id,
        "repeats": args.repeats,
        "sweep_range": list(range(args.min_facts, args.max_facts + 1)),
        "question": QD3_QUESTION,
        "critical_missing": CRITICAL_MISSING,
        "variants": [],
    }

    for mf in range(args.min_facts, args.max_facts + 1):
        print(f"\n{'='*70}")
        print(f"  max_facts = {mf}")
        print(f"{'='*70}")

        proc = None
        if not external_api:
            print(f"  Starting API server with ROUTE7_RECOGNITION_MEMORY_MAX_FACTS={mf}...")
            proc = start_api_server(mf, args.port)
            if not _wait_for_api(api_url, max_wait=90):
                print(f"  ❌ API failed to start for max_facts={mf}")
                stop_api_server(proc)
                continue
            print(f"  ✅ API ready")
        else:
            # For external API, set env var (won't affect already-running server)
            os.environ["ROUTE7_RECOGNITION_MEMORY_MAX_FACTS"] = str(mf)

        try:
            variant = run_qd3_with_max_facts(
                api_url=api_url,
                group_id=group_id,
                max_facts=mf,
                repeats=args.repeats,
                no_auth=args.no_auth,
                include_context=True,
            )
            results["variants"].append(variant)
        finally:
            if proc:
                print(f"  Stopping API server...")
                stop_api_server(proc)

    # ── Summary table ───────────────────────────────────────────────
    print(f"\n{'='*70}")
    print("SUMMARY: Recognition Memory Max Facts Sweep")
    print(f"{'='*70}")
    print(f"{'max_facts':>10} | {'avg_kw':>8} | {'best_kw':>8} | {'avg_crit':>9} | {'best_crit':>10}")
    print(f"{'-'*10}-+-{'-'*8}-+-{'-'*8}-+-{'-'*9}-+-{'-'*10}")
    for v in results["variants"]:
        print(f"{v['max_facts']:>10} | {v['avg_keyword_hits']:>8} | {v['best_keyword_hits']:>8} | {v['avg_critical_hits']:>9} | {v['best_critical_hits']:>10}")

    # Save results
    out_path = Path(f"experiment_max_facts_sweep_{ts}.json")
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"\n📁 Results saved to: {out_path}")

    # Determine best
    if results["variants"]:
        best = max(results["variants"], key=lambda v: (v["avg_critical_hits"], v["avg_keyword_hits"]))
        print(f"\n🏆 Best max_facts = {best['max_facts']} (avg critical: {best['avg_critical_hits']}, avg keywords: {best['avg_keyword_hits']})")


if __name__ == "__main__":
    main()
