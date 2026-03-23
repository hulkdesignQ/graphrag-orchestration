"""
Evidoc Load Test — Locust configuration
========================================
Simulates realistic user traffic against the Evidoc API.

Usage:
  # Smoke test (1-2 users against production)
  locust -f locustfile.py --host https://app.evidoc.hulkdesign.com -u 2 -r 1 -t 2m

  # Light load test (10 users)
  locust -f locustfile.py --host https://app.evidoc.hulkdesign.com -u 10 -r 2 -t 5m

  # Autoscaling validation (50 users, ramp over 2 min)
  locust -f locustfile.py --host https://app.evidoc.hulkdesign.com -u 50 -r 5 -t 10m

  # Web UI (default http://localhost:8089)
  locust -f locustfile.py --host https://app.evidoc.hulkdesign.com

Environment variables:
  EVIDOC_AUTH_TOKEN  — EasyAuth session token (from /.auth/login/aad exchange)
  EVIDOC_AAD_TOKEN   — Azure AD access token (auto-exchanged for session token)
  EVIDOC_GROUP_ID   — group_id header for auth-disabled envs (default: load-test)
  EVIDOC_USER_ID    — user_id header (default: locust-user)
  EVIDOC_FOLDER_ID  — scope queries to a specific folder (optional)

  Auth precedence: EVIDOC_AUTH_TOKEN > EVIDOC_AAD_TOKEN (exchanged) > X-Group-ID fallback
"""

import os
import random

import requests
from locust import HttpUser, between, tag, task

# --- Questions that work on any indexed corpus ---
GENERAL_QUESTIONS = [
    "What are the main topics covered in my documents?",
    "Summarize the key points across all documents.",
    "What dates or deadlines are mentioned?",
    "Are there any financial figures or amounts mentioned?",
    "What parties or organizations are involved?",
    "What obligations or requirements are described?",
    "Are there any risk factors mentioned?",
    "What are the confidentiality terms?",
]

# --- Follow-up questions (used after an initial query) ---
FOLLOW_UP_QUESTIONS = [
    "Can you provide more details on that?",
    "What are the specific numbers involved?",
    "Are there any exceptions to this?",
    "What is the timeline for this?",
    "Who is responsible for this?",
]


class EvidocUser(HttpUser):
    """Simulates a typical Evidoc user session: browse files, ask questions."""

    wait_time = between(3, 8)

    def on_start(self):
        # Auth strategy: EasyAuth session token > AAD token exchange > X-Group-ID fallback
        session_token = os.environ.get("EVIDOC_AUTH_TOKEN")
        aad_token = os.environ.get("EVIDOC_AAD_TOKEN")

        if session_token:
            self.client.headers["X-ZUMO-AUTH"] = session_token
        elif aad_token:
            # Exchange AAD access token for EasyAuth session token
            resp = requests.post(
                f"{self.host}/.auth/login/aad",
                json={"access_token": aad_token},
                timeout=10,
            )
            if resp.status_code == 200:
                token = resp.json().get("authenticationToken", "")
                self.client.headers["X-ZUMO-AUTH"] = token
            else:
                raise RuntimeError(f"EasyAuth token exchange failed: {resp.status_code} {resp.text}")
        else:
            self.client.headers["X-Group-ID"] = os.environ.get("EVIDOC_GROUP_ID", "load-test")
            self.client.headers["X-User-ID"] = os.environ.get("EVIDOC_USER_ID", "locust-user")

        self.folder_id = os.environ.get("EVIDOC_FOLDER_ID")

    # ------------------------------------------------------------------ #
    # Health & navigation (lightweight, high frequency)
    # ------------------------------------------------------------------ #

    @tag("health")
    @task(3)
    def health_check(self):
        self.client.get("/health", name="/health")

    @tag("browse")
    @task(4)
    def list_files(self):
        self.client.get("/list_uploaded", name="/list_uploaded")

    @tag("browse")
    @task(3)
    def list_folders(self):
        self.client.get("/folders", name="/folders")

    # ------------------------------------------------------------------ #
    # Chat queries via frontend endpoint (main user flow)
    # ------------------------------------------------------------------ #

    @tag("chat")
    @task(8)
    def chat_query(self):
        question = random.choice(GENERAL_QUESTIONS)
        overrides = {"retrieval_mode": "hybrid"}
        if self.folder_id:
            overrides["folder_id"] = self.folder_id

        with self.client.post(
            "/chat",
            name="/chat (initial)",
            json={
                "messages": [{"role": "user", "content": question}],
                "context": {"overrides": overrides},
                "session_state": None,
            },
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code == 429:
                resp.failure("Rate limited")
            else:
                resp.failure(f"HTTP {resp.status_code}")

    @tag("chat")
    @task(4)
    def chat_follow_up(self):
        """Two-turn conversation: initial question → follow-up."""
        question = random.choice(GENERAL_QUESTIONS)
        overrides = {"retrieval_mode": "hybrid"}
        if self.folder_id:
            overrides["folder_id"] = self.folder_id

        resp = self.client.post(
            "/chat",
            name="/chat (initial for follow-up)",
            json={
                "messages": [{"role": "user", "content": question}],
                "context": {"overrides": overrides},
                "session_state": None,
            },
        )
        if resp.status_code != 200:
            return

        data = resp.json()
        assistant_msg = data.get("message", {}).get("content", "")

        # Use server-suggested follow-up if available, else pick a generic one
        followups = data.get("context", {}).get("followup_questions", [])
        follow_up = random.choice(followups) if followups else random.choice(FOLLOW_UP_QUESTIONS)

        self.client.post(
            "/chat",
            name="/chat (follow-up)",
            json={
                "messages": [
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": assistant_msg},
                    {"role": "user", "content": follow_up},
                ],
                "context": {"overrides": overrides},
                "session_state": None,
            },
        )

    # ------------------------------------------------------------------ #
    # Hybrid query endpoint (API-style)
    # ------------------------------------------------------------------ #

    @tag("hybrid")
    @task(5)
    def hybrid_query(self):
        question = random.choice(GENERAL_QUESTIONS)
        body = {"query": question}
        if self.folder_id:
            body["folder_id"] = self.folder_id

        with self.client.post(
            "/hybrid/query",
            name="/hybrid/query",
            json=body,
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code == 429:
                resp.failure("Rate limited")
            else:
                resp.failure(f"HTTP {resp.status_code}")

    # ------------------------------------------------------------------ #
    # Models endpoint (lightweight metadata call)
    # ------------------------------------------------------------------ #

    @tag("metadata")
    @task(2)
    def chat_models(self):
        self.client.get("/chat/models", name="/chat/models")
