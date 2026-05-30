"""Unit tests for the batch methods on :class:`AIOrchestrator`.

The Anthropic SDK's ``client.messages.batches`` namespace is mocked
out so these tests exercise the orchestrator's contract (envelope
shape, error mapping, results streaming) without any network. The
parser side is covered separately in ``test_batch.py``.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

from start_green_stay_green.ai.batch import BatchPoll
from start_green_stay_green.ai.batch import BatchResultsBundle
from start_green_stay_green.ai.batch import BatchSubmission
from start_green_stay_green.ai.batch import ToolUseBatchRequest
from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.ai.orchestrator import GenerationError
from start_green_stay_green.ai.orchestrator import ToolUseResult


def _wire_batches(orchestrator: AIOrchestrator) -> MagicMock:
    """Replace the cached async client with a mock exposing ``messages.batches``.

    Returns the ``batches`` mock so tests can ``.create``/``.retrieve``/
    ``.results`` against it directly. Bypasses the lazy
    ``_get_async_client`` construction so no real ``AsyncAnthropic``
    instance is created.
    """
    client = MagicMock()
    orchestrator._async_client = client
    batches: MagicMock = client.messages.batches
    return batches


def _request(custom_id: str = "subagent:a") -> ToolUseBatchRequest:
    return ToolUseBatchRequest(
        custom_id=custom_id,
        prompt="hello",
        system_blocks=[{"type": "text", "text": "S"}],
        tool_schema={
            "name": "report_tuning",
            "input_schema": {"type": "object"},
        },
    )


@pytest.fixture
def orchestrator() -> AIOrchestrator:
    """Bare orchestrator with no real client yet — tests inject one."""
    return AIOrchestrator(api_key="sk-test", max_retries=1, retry_delay=0.01)


class TestSubmitToolUseBatch:
    """``submit_tool_use_batch`` wraps the SDK and validates inputs."""

    @pytest.mark.asyncio
    async def test_returns_batch_submission_with_id_and_custom_ids(
        self,
        orchestrator: AIOrchestrator,
    ) -> None:
        batches = _wire_batches(orchestrator)
        batches.create = AsyncMock(return_value=MagicMock(id="msgbatch_42"))

        result = await orchestrator.submit_tool_use_batch(
            [_request("subagent:a"), _request("subagent:b")],
        )

        assert isinstance(result, BatchSubmission)
        assert result.batch_id == "msgbatch_42"
        assert result.custom_ids == ["subagent:a", "subagent:b"]
        assert result.submitted_at  # ISO timestamp populated

    @pytest.mark.asyncio
    async def test_request_envelope_carries_tool_choice_and_system(
        self,
        orchestrator: AIOrchestrator,
    ) -> None:
        """Each submitted request mirrors ``_call_tool_api_async``'s shape."""
        batches = _wire_batches(orchestrator)
        batches.create = AsyncMock(return_value=MagicMock(id="msgbatch_x"))

        await orchestrator.submit_tool_use_batch([_request("subagent:a")])

        kwargs = batches.create.await_args.kwargs
        payload = kwargs["requests"]
        assert len(payload) == 1
        envelope = payload[0]
        assert envelope["custom_id"] == "subagent:a"
        params = envelope["params"]
        assert params["model"] == orchestrator.model
        assert params["tool_choice"] == {"type": "tool", "name": "report_tuning"}
        assert params["system"] == [{"type": "text", "text": "S"}]
        assert params["messages"] == [{"role": "user", "content": "hello"}]

    @pytest.mark.asyncio
    async def test_empty_request_list_raises(
        self,
        orchestrator: AIOrchestrator,
    ) -> None:
        with pytest.raises(ValueError, match="at least one"):
            await orchestrator.submit_tool_use_batch([])

    @pytest.mark.asyncio
    async def test_duplicate_custom_id_raises(
        self,
        orchestrator: AIOrchestrator,
    ) -> None:
        with pytest.raises(ValueError, match="unique custom_id"):
            await orchestrator.submit_tool_use_batch(
                [
                    _request("dup"),
                    _request("dup"),
                ]
            )

    @pytest.mark.asyncio
    async def test_missing_tool_schema_name_raises_generation_error(
        self,
        orchestrator: AIOrchestrator,
    ) -> None:
        """Empty / missing ``tool_schema['name']`` fails close to the caller.

        Without this guard the API would return an opaque HTTP 400
        wrapped in a generic ``GenerationError("Batch submission
        failed")`` — much harder to debug than a named-field error
        that points at the offending request.
        """
        bad_request = ToolUseBatchRequest(
            custom_id="subagent:nameless",
            prompt="hi",
            system_blocks=[{"type": "text", "text": "S"}],
            tool_schema={"input_schema": {"type": "object"}},  # no "name"
        )
        with pytest.raises(GenerationError, match="non-empty 'name'"):
            await orchestrator.submit_tool_use_batch([bad_request])


class TestPollBatch:
    """``poll_batch`` snapshots the SDK ``BatchObject`` into ``BatchPoll``."""

    @pytest.mark.asyncio
    async def test_returns_batch_poll_with_counts(
        self,
        orchestrator: AIOrchestrator,
    ) -> None:
        batches = _wire_batches(orchestrator)
        counts = MagicMock(processing=2, succeeded=5, errored=1)
        batches.retrieve = AsyncMock(
            return_value=MagicMock(
                processing_status="in_progress",
                request_counts=counts,
            ),
        )

        poll = await orchestrator.poll_batch("msgbatch_42")

        assert isinstance(poll, BatchPoll)
        assert poll.batch_id == "msgbatch_42"
        assert poll.status == "in_progress"
        assert (poll.processing_count, poll.succeeded_count, poll.errored_count) == (
            2,
            5,
            1,
        )
        assert not poll.is_ended

    @pytest.mark.asyncio
    async def test_ended_status_flips_is_ended(
        self,
        orchestrator: AIOrchestrator,
    ) -> None:
        batches = _wire_batches(orchestrator)
        batches.retrieve = AsyncMock(
            return_value=MagicMock(
                processing_status="ended",
                request_counts=MagicMock(processing=0, succeeded=8, errored=0),
            ),
        )
        poll = await orchestrator.poll_batch("msgbatch_42")
        assert poll.is_ended

    @pytest.mark.asyncio
    async def test_empty_batch_id_raises(
        self,
        orchestrator: AIOrchestrator,
    ) -> None:
        with pytest.raises(ValueError, match="non-empty batch_id"):
            await orchestrator.poll_batch("")

    @pytest.mark.asyncio
    async def test_canceled_and_expired_counts_threaded_through(
        self,
        orchestrator: AIOrchestrator,
    ) -> None:
        """Phase 5b reconciliation needs canceled/expired distinct from errored."""
        batches = _wire_batches(orchestrator)
        batches.retrieve = AsyncMock(
            return_value=MagicMock(
                processing_status="ended",
                request_counts=MagicMock(
                    processing=0,
                    succeeded=5,
                    errored=1,
                    canceled=2,
                    expired=3,
                ),
            ),
        )

        poll = await orchestrator.poll_batch("msgbatch_42")

        assert poll.errored_count == 1
        assert poll.canceled_count == 2
        assert poll.expired_count == 3


class TestFetchBatchResults:
    """``fetch_batch_results`` folds a streamed result iterable into bundle maps."""

    @pytest.mark.asyncio
    async def test_streams_succeeded_into_successes_map(
        self,
        orchestrator: AIOrchestrator,
    ) -> None:
        batches = _wire_batches(orchestrator)
        batches.results = AsyncMock(
            return_value=[
                _success_entry("subagent:a"),
                _success_entry("subagent:b"),
            ]
        )

        bundle = await orchestrator.fetch_batch_results("msgbatch_x")

        assert isinstance(bundle, BatchResultsBundle)
        assert set(bundle.successes) == {"subagent:a", "subagent:b"}
        assert bundle.failures == {}
        assert isinstance(bundle.successes["subagent:a"], ToolUseResult)

    @pytest.mark.asyncio
    async def test_mixed_stream_partitions_correctly(
        self,
        orchestrator: AIOrchestrator,
    ) -> None:
        batches = _wire_batches(orchestrator)
        batches.results = AsyncMock(
            return_value=[
                _success_entry("subagent:a"),
                _failure_entry("subagent:b", "errored"),
                _failure_entry("subagent:c", "expired"),
            ]
        )

        bundle = await orchestrator.fetch_batch_results("msgbatch_x")

        assert set(bundle.successes) == {"subagent:a"}
        assert set(bundle.failures) == {"subagent:b", "subagent:c"}
        assert bundle.failures["subagent:b"].result_type == "errored"

    @pytest.mark.asyncio
    async def test_empty_batch_id_raises(
        self,
        orchestrator: AIOrchestrator,
    ) -> None:
        with pytest.raises(ValueError, match="non-empty batch_id"):
            await orchestrator.fetch_batch_results("")

    @pytest.mark.asyncio
    async def test_unparseable_entry_propagates_generation_error(
        self,
        orchestrator: AIOrchestrator,
    ) -> None:
        """A stream entry the parser rejects aborts the fold (current contract).

        ``parse_batch_result_entry`` raises ``GenerationError`` only
        for shapes so malformed that no ``custom_id`` can be
        recovered (per-request failures land in ``failures`` instead).
        Pin the propagation so a future refactor that swallows the
        error in :meth:`fetch_batch_results` is loud, not silent.
        """
        batches = _wire_batches(orchestrator)
        batches.results = AsyncMock(
            return_value=[
                _success_entry("subagent:a"),
                {"custom_id": "", "result": {}},  # missing custom_id
            ]
        )
        with pytest.raises(GenerationError, match="custom_id"):
            await orchestrator.fetch_batch_results("msgbatch_x")


class TestBatchSDKErrorMapping:
    """SDK-side exceptions get wrapped in ``GenerationError`` for the caller."""

    @pytest.mark.asyncio
    async def test_submission_failure_wraps_in_generation_error(
        self,
        orchestrator: AIOrchestrator,
    ) -> None:
        batches = _wire_batches(orchestrator)
        batches.create = AsyncMock(side_effect=RuntimeError("boom"))

        with pytest.raises(GenerationError, match="Batch submission failed"):
            await orchestrator.submit_tool_use_batch([_request()])

    @pytest.mark.asyncio
    async def test_poll_failure_wraps_in_generation_error(
        self,
        orchestrator: AIOrchestrator,
    ) -> None:
        """``poll_batch`` lifts SDK errors into ``GenerationError`` like submit does.

        Without this test the orchestrator's wrapper around
        ``client.messages.batches.retrieve`` is uncovered; a refactor
        that drops the wrapper would silently surface raw SDK
        exceptions to callers.
        """
        batches = _wire_batches(orchestrator)
        batches.retrieve = AsyncMock(side_effect=RuntimeError("upstream gone"))

        with pytest.raises(
            GenerationError,
            match="Batch retrieve failed for msgbatch_x",
        ):
            await orchestrator.poll_batch("msgbatch_x")

    @pytest.mark.asyncio
    async def test_fetch_failure_wraps_in_generation_error(
        self,
        orchestrator: AIOrchestrator,
    ) -> None:
        """``fetch_batch_results`` lifts stream-open errors into ``GenerationError``.

        Pins the SDK-error → ``GenerationError`` contract for the third
        SDK-touching method so all three error paths
        (``submit`` / ``poll`` / ``fetch``) are uniformly covered.
        """
        batches = _wire_batches(orchestrator)
        batches.results = AsyncMock(side_effect=RuntimeError("stream closed"))

        with pytest.raises(
            GenerationError,
            match="Batch results stream failed for msgbatch_x",
        ):
            await orchestrator.fetch_batch_results("msgbatch_x")


def _success_entry(custom_id: str) -> dict[str, Any]:
    """Minimal succeeded-entry dict the parser will lift to a ``ToolUseResult``."""
    return {
        "custom_id": custom_id,
        "result": {
            "type": "succeeded",
            "message": {
                "id": f"msg_{custom_id}",
                "model": "claude-sonnet",
                "content": [
                    {
                        "type": "tool_use",
                        "name": "report_tuning",
                        "input": {"tuned_content": "X", "changes": []},
                    },
                ],
                "usage": {"input_tokens": 1, "output_tokens": 1},
            },
        },
    }


def _failure_entry(custom_id: str, result_type: str) -> dict[str, Any]:
    return {
        "custom_id": custom_id,
        "result": {
            "type": result_type,
            "error": {"message": f"upstream {result_type}"},
        },
    }
