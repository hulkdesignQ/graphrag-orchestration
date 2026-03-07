"""Unit tests for the Azure Translator query translation feature.

Tests:
- TranslatorService (mock HTTP)
- TranslationResult dataclass
- credit_schedule.compute_translation_credits
- TokenAccumulator translation tracking
- Orchestrator _maybe_translate_query (mock translator + Neo4j)
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# ============================================================================
# 1. credit_schedule
# ============================================================================


class TestTranslationCredits:
    def test_small_text(self):
        from src.core.services.credit_schedule import compute_translation_credits
        # 100 chars → $0.001 → 1 credit (minimum)
        assert compute_translation_credits(100) == 1

    def test_medium_text(self):
        from src.core.services.credit_schedule import compute_translation_credits
        # 10,000 chars → $0.0001 * 10 = $0.10 → 100 credits
        assert compute_translation_credits(10_000) == 100

    def test_one_million_chars(self):
        from src.core.services.credit_schedule import compute_translation_credits
        # 1M chars → $10 → 10,000 credits
        assert compute_translation_credits(1_000_000) == 10_000

    def test_zero_chars(self):
        from src.core.services.credit_schedule import compute_translation_credits
        # 0 chars → $0 → but minimum 1 credit
        assert compute_translation_credits(0) == 1


# ============================================================================
# 2. UsageRecord model
# ============================================================================


class TestUsageRecordTranslation:
    def test_translation_usage_type(self):
        from src.core.models.usage import UsageType
        assert UsageType.TRANSLATION == "translation"

    def test_translation_fields(self):
        from src.core.models.usage import UsageRecord
        record = UsageRecord(
            partition_id="test-group",
            usage_type="translation",
            characters_translated=500,
            detected_language="ja",
            was_translated=True,
        )
        assert record.characters_translated == 500
        assert record.detected_language == "ja"
        assert record.was_translated is True

    def test_default_translation_fields_are_none(self):
        from src.core.models.usage import UsageRecord
        record = UsageRecord(
            partition_id="test-group",
            usage_type="llm_completion",
        )
        assert record.characters_translated is None
        assert record.detected_language is None
        assert record.was_translated is None


# ============================================================================
# 3. TokenAccumulator
# ============================================================================


class TestTokenAccumulatorTranslation:
    def test_add_translation(self):
        from src.core.services.token_accumulator import TokenAccumulator
        acc = TokenAccumulator()
        acc.add_translation(characters=1000, detected_language="ja", was_translated=True)
        snap = acc.snapshot()
        assert snap["translation_chars"] == 1000
        assert snap["detected_language"] == "ja"
        assert snap["was_translated"] is True

    def test_no_translation(self):
        from src.core.services.token_accumulator import TokenAccumulator
        acc = TokenAccumulator()
        snap = acc.snapshot()
        assert snap["translation_chars"] == 0
        assert snap["detected_language"] is None
        assert snap["was_translated"] is False

    def test_translation_credits_in_total(self):
        from src.core.services.token_accumulator import TokenAccumulator
        acc = TokenAccumulator()
        # Add LLM usage
        acc.add(model="gpt-4o", prompt_tokens=1000, completion_tokens=500)
        credits_without_translation = acc.compute_credits()

        # Add translation
        acc.add_translation(characters=10_000, detected_language="fr", was_translated=True)
        credits_with_translation = acc.compute_credits()

        # Translation should add credits
        assert credits_with_translation > credits_without_translation

    def test_same_language_no_credits(self):
        from src.core.services.token_accumulator import TokenAccumulator
        acc = TokenAccumulator()
        # was_translated=False, 0 chars → no translation credits
        acc.add_translation(characters=0, detected_language="en", was_translated=False)
        snap = acc.snapshot()
        assert snap["translation_chars"] == 0
        # Only minimum credits from empty accumulator
        assert snap["credits_used"] == 0


# ============================================================================
# 4. TranslatorService
# ============================================================================


class TestTranslatorService:
    def test_not_available_without_endpoint(self):
        from src.worker.services.translator_service import TranslatorService
        svc = TranslatorService(endpoint="", region="swedencentral")
        assert svc.is_available is False

    def test_available_with_endpoint(self):
        from src.worker.services.translator_service import TranslatorService
        svc = TranslatorService(
            endpoint="https://translator.example.com",
            region="swedencentral",
        )
        assert svc.is_available is True

    @pytest.mark.asyncio
    async def test_returns_original_when_not_available(self):
        from src.worker.services.translator_service import TranslatorService
        svc = TranslatorService(endpoint="", region="swedencentral")
        result = await svc.detect_and_translate("hello", target_lang="en")
        assert result.translated_text == "hello"
        assert result.was_translated is False
        assert result.characters == 0

    @pytest.mark.asyncio
    async def test_translates_japanese_to_english(self):
        from src.worker.services.translator_service import TranslatorService

        # Mock the Azure Translator API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[{
            "detectedLanguage": {"language": "ja", "score": 1.0},
            "translations": [{"text": "What is the contract period?", "to": "en"}],
        }])
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_response)

        svc = TranslatorService(
            endpoint="https://translator.example.com",
            region="swedencentral",
        )

        with patch.object(svc, "_get_token", return_value="fake-token"), \
             patch.object(svc, "_get_session", return_value=mock_session):
            result = await svc.detect_and_translate("契約期間はどのくらいですか？", target_lang="en")

        assert result.detected_language == "ja"
        assert result.translated_text == "What is the contract period?"
        assert result.was_translated is True
        assert result.characters == len("契約期間はどのくらいですか？")

    @pytest.mark.asyncio
    async def test_skips_translation_when_same_language(self):
        from src.worker.services.translator_service import TranslatorService

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[{
            "detectedLanguage": {"language": "en", "score": 1.0},
            "translations": [{"text": "What is the contract period?", "to": "en"}],
        }])
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_response)

        svc = TranslatorService(
            endpoint="https://translator.example.com",
            region="swedencentral",
        )

        with patch.object(svc, "_get_token", return_value="fake-token"), \
             patch.object(svc, "_get_session", return_value=mock_session):
            result = await svc.detect_and_translate("What is the contract period?", target_lang="en")

        assert result.detected_language == "en"
        assert result.was_translated is False
        assert result.translated_text == "What is the contract period?"
        assert result.characters == 0  # No chars billed when same language

    @pytest.mark.asyncio
    async def test_handles_api_error_gracefully(self):
        from src.worker.services.translator_service import TranslatorService

        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_response)

        svc = TranslatorService(
            endpoint="https://translator.example.com",
            region="swedencentral",
        )

        with patch.object(svc, "_get_token", return_value="fake-token"), \
             patch.object(svc, "_get_session", return_value=mock_session):
            result = await svc.detect_and_translate("テスト", target_lang="en")

        # Should return original text on error
        assert result.translated_text == "テスト"
        assert result.was_translated is False
        assert result.characters == 0


# ============================================================================
# 5. Orchestrator _maybe_translate_query
# ============================================================================


class TestOrchestratorTranslation:
    @pytest.mark.asyncio
    async def test_translates_when_language_differs(self):
        """Query in Japanese + documents in English → translate to English."""
        from src.worker.services.translator_service import TranslationResult
        from src.core.services.token_accumulator import TokenAccumulator

        # Build a minimal mock pipeline
        pipeline = MagicMock()
        pipeline.group_id = "test-group"
        pipeline._async_neo4j = AsyncMock()
        pipeline._async_neo4j.run_query = AsyncMock(return_value=[{"lang": "en"}])

        # Import the method
        from src.worker.hybrid_v2.orchestrator import HybridPipeline
        pipeline._get_document_language = HybridPipeline._get_document_language.__get__(pipeline)
        pipeline._maybe_translate_query = HybridPipeline._maybe_translate_query.__get__(pipeline)

        mock_result = TranslationResult(
            original_text="契約期間は？",
            translated_text="What is the contract period?",
            detected_language="ja",
            target_language="en",
            was_translated=True,
            characters=6,
        )

        with patch(
            "src.worker.services.translator_service.get_translator_service"
        ) as mock_get:
            mock_svc = AsyncMock()
            mock_svc.is_available = True
            mock_svc.detect_and_translate = AsyncMock(return_value=mock_result)
            mock_get.return_value = mock_svc

            acc = TokenAccumulator()
            text, lang, translated = await pipeline._maybe_translate_query("契約期間は？", accumulator=acc)

        assert text == "What is the contract period?"
        assert lang == "ja"
        assert translated is True
        assert acc.snapshot()["translation_chars"] == 6

    @pytest.mark.asyncio
    async def test_no_translation_when_same_language(self):
        """Query in English + documents in English → no translation."""
        from src.worker.services.translator_service import TranslationResult
        from src.core.services.token_accumulator import TokenAccumulator

        pipeline = MagicMock()
        pipeline.group_id = "test-group"
        pipeline._async_neo4j = AsyncMock()
        pipeline._async_neo4j.run_query = AsyncMock(return_value=[{"lang": "en"}])

        from src.worker.hybrid_v2.orchestrator import HybridPipeline
        pipeline._get_document_language = HybridPipeline._get_document_language.__get__(pipeline)
        pipeline._maybe_translate_query = HybridPipeline._maybe_translate_query.__get__(pipeline)

        mock_result = TranslationResult(
            original_text="What is the contract period?",
            translated_text="What is the contract period?",
            detected_language="en",
            target_language="en",
            was_translated=False,
            characters=0,
        )

        with patch(
            "src.worker.services.translator_service.get_translator_service"
        ) as mock_get:
            mock_svc = AsyncMock()
            mock_svc.is_available = True
            mock_svc.detect_and_translate = AsyncMock(return_value=mock_result)
            mock_get.return_value = mock_svc

            acc = TokenAccumulator()
            text, lang, translated = await pipeline._maybe_translate_query(
                "What is the contract period?", accumulator=acc
            )

        assert text == "What is the contract period?"
        assert lang == "en"
        assert translated is False
        assert acc.snapshot()["translation_chars"] == 0

    @pytest.mark.asyncio
    async def test_fallback_when_translator_unavailable(self):
        """No translator configured → pass query through unchanged."""
        from src.core.services.token_accumulator import TokenAccumulator

        pipeline = MagicMock()
        pipeline.group_id = "test-group"
        pipeline._async_neo4j = AsyncMock()
        pipeline._async_neo4j.run_query = AsyncMock(return_value=[{"lang": "en"}])

        from src.worker.hybrid_v2.orchestrator import HybridPipeline
        pipeline._get_document_language = HybridPipeline._get_document_language.__get__(pipeline)
        pipeline._maybe_translate_query = HybridPipeline._maybe_translate_query.__get__(pipeline)

        with patch(
            "src.worker.services.translator_service.get_translator_service"
        ) as mock_get:
            mock_svc = MagicMock()
            mock_svc.is_available = False
            mock_get.return_value = mock_svc

            acc = TokenAccumulator()
            text, lang, translated = await pipeline._maybe_translate_query("テスト", accumulator=acc)

        assert text == "テスト"
        assert lang is None
        assert translated is False

    @pytest.mark.asyncio
    async def test_doc_language_cache(self):
        """Document language should be cached after first call."""
        from src.worker.hybrid_v2.orchestrator import HybridPipeline

        # Use a SimpleNamespace so hasattr behaves correctly (no auto-create)
        from types import SimpleNamespace
        pipeline = SimpleNamespace(
            group_id="test-group",
            _async_neo4j=AsyncMock(),
        )
        pipeline._async_neo4j.run_query = AsyncMock(return_value=[{"lang": "en"}])
        pipeline._get_document_language = HybridPipeline._get_document_language.__get__(pipeline)

        # First call — queries Neo4j
        lang1 = await pipeline._get_document_language()
        assert lang1 == "en"
        assert pipeline._async_neo4j.run_query.call_count == 1

        # Second call — uses cache
        lang2 = await pipeline._get_document_language()
        assert lang2 == "en"
        assert pipeline._async_neo4j.run_query.call_count == 1  # Still 1, cached
