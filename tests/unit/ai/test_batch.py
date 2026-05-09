"""Unit tests for the batch primitives in ``ai/batch.py``.

The orchestrator's batch methods are integration concerns covered
elsewhere; this file pins the pure-data parser
(:func:`parse_batch_result_entry`) and the dataclass shapes against
both real-SDK-shaped payloads (Pydantic-style attribute access) and
plain-dict test doubles.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from start_green_stay_green.ai.batch import BatchError
from start_green_stay_green.ai.batch import BatchPoll
from start_green_stay_green.ai.batch import BatchResultsBundle
from start_green_stay_green.ai.batch import BatchSubmission
from start_green_stay_green.ai.batch import ToolUseBatchRequest
from start_green_stay_green.ai.batch import parse_batch_result_entry
from start_green_stay_green.ai.orchestrator import GenerationError
from start_green_stay_green.ai.orchestrator import TokenUsage
from start_green_stay_green.ai.orchestrator import ToolUseResult

_DEFAULT_USAGE: dict[str, int] = {
    "input_tokens": 100,
    "output_tokens": 50,
    "cache_read_input_tokens": 10,
    "cache_creation_input_tokens": 5,
}


def _success_entry(
    custom_id: str = "subagent:foo",
    *,
    tool_input: dict[str, Any] | None = None,
    usage: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Plain-dict double of one streamed batch result on the success path."""
    return {
        "custom_id": custom_id,
        "result": {
            "type": "succeeded",
            "message": {
                "id": "msg_123",
                "model": "claude-sonnet",
                "content": [
                    {
                        "type": "tool_use",
                        "name": "report_tuning",
                        "input": tool_input or {"tuned_content": "X", "changes": ["c"]},
                    },
                ],
                "usage": usage if usage is not None else dict(_DEFAULT_USAGE),
            },
        },
    }


class TestParseBatchResultEntrySuccess:
    """Successful entries lift into ``ToolUseResult`` with full telemetry."""

    def test_returns_tool_use_result_for_succeeded_entry(self) -> None:
        custom_id, outcome = parse_batch_result_entry(_success_entry())

        assert custom_id == "subagent:foo"
        assert isinstance(outcome, ToolUseResult)
        assert outcome.tool_name == "report_tuning"
        assert outcome.tool_input == {"tuned_content": "X", "changes": ["c"]}

    def test_token_usage_is_threaded_through(self) -> None:
        _, outcome = parse_batch_result_entry(_success_entry())
        assert isinstance(outcome, ToolUseResult)

        assert outcome.token_usage.input_tokens == 100
        assert outcome.token_usage.output_tokens == 50

    def test_cache_telemetry_is_surfaced(self) -> None:
        """Phase 2c cache columns reach batch users too — pin that."""
        _, outcome = parse_batch_result_entry(_success_entry())
        assert isinstance(outcome, ToolUseResult)

        assert outcome.cache_read_tokens == 10
        assert outcome.cache_creation_tokens == 5

    def test_works_with_attribute_access_payload(self) -> None:
        """Real SDK responses expose attributes; tests sometimes pass dicts.

        Mix the two forms in a single payload to verify
        ``_extract_attr`` does not silently prefer one shape.
        """

        @dataclass
        class _Usage:
            input_tokens: int = 7
            output_tokens: int = 3
            cache_read_input_tokens: int = 0
            cache_creation_input_tokens: int = 0

        @dataclass
        class _ToolBlock:
            type: str = "tool_use"
            name: str = "report_tuning"
            input: dict[str, Any] | None = None

        @dataclass
        class _Message:
            id: str = "msg_attr"
            model: str = "claude"
            content: list[Any] | None = None
            usage: _Usage | None = None

        @dataclass
        class _Result:
            type: str = "succeeded"
            message: _Message | None = None

        @dataclass
        class _Entry:
            custom_id: str = "skill:bar"
            result: _Result | None = None

        entry = _Entry(
            result=_Result(
                message=_Message(
                    content=[
                        _ToolBlock(input={"tuned_content": "Y", "changes": []}),
                    ],
                    usage=_Usage(),
                ),
            ),
        )

        custom_id, outcome = parse_batch_result_entry(entry)
        assert custom_id == "skill:bar"
        assert isinstance(outcome, ToolUseResult)
        assert outcome.tool_input == {"tuned_content": "Y", "changes": []}
        assert outcome.message_id == "msg_attr"


class TestParseBatchResultEntryFailures:
    """Per-request failure types do *not* raise — they return BatchError."""

    @pytest.mark.parametrize("failure_type", ["errored", "canceled", "expired"])
    def test_failure_types_yield_batch_error(self, failure_type: str) -> None:
        entry = {
            "custom_id": "subagent:bad",
            "result": {
                "type": failure_type,
                "error": {"message": f"upstream {failure_type}"},
            },
        }

        custom_id, outcome = parse_batch_result_entry(entry)
        assert custom_id == "subagent:bad"
        assert isinstance(outcome, BatchError)
        assert outcome.result_type == failure_type
        assert f"upstream {failure_type}" in outcome.message

    def test_unknown_result_type_is_recorded_as_batcherror(self) -> None:
        entry = {
            "custom_id": "subagent:weird",
            "result": {"type": "future_status_we_havent_heard_of"},
        }

        _, outcome = parse_batch_result_entry(entry)
        assert isinstance(outcome, BatchError)
        assert outcome.result_type == "future_status_we_havent_heard_of"

    def test_missing_custom_id_raises_generation_error(self) -> None:
        with pytest.raises(GenerationError, match="custom_id"):
            parse_batch_result_entry({"custom_id": "", "result": {}})

    def test_missing_tool_use_block_raises(self) -> None:
        entry = {
            "custom_id": "subagent:empty",
            "result": {
                "type": "succeeded",
                "message": {
                    "id": "msg_x",
                    "model": "claude",
                    "content": [{"type": "text", "text": "no tool here"}],
                    "usage": {"input_tokens": 1, "output_tokens": 1},
                },
            },
        }
        with pytest.raises(GenerationError, match="ToolUseBlock"):
            parse_batch_result_entry(entry)

    def test_non_dict_tool_input_raises(self) -> None:
        entry = _success_entry()
        entry["result"]["message"]["content"][0]["input"] = "not-a-dict"
        with pytest.raises(GenerationError, match="JSON object"):
            parse_batch_result_entry(entry)


class TestBatchPoll:
    """The :class:`BatchPoll` snapshot exposes a clear is_ended hook."""

    def test_is_ended_true_only_for_status_ended(self) -> None:
        ended = BatchPoll(
            batch_id="b",
            status="ended",
            processing_count=0,
            succeeded_count=3,
            errored_count=0,
        )
        in_progress = BatchPoll(
            batch_id="b",
            status="in_progress",
            processing_count=3,
            succeeded_count=0,
            errored_count=0,
        )
        canceling = BatchPoll(
            batch_id="b",
            status="canceling",
            processing_count=0,
            succeeded_count=2,
            errored_count=1,
        )

        assert ended.is_ended
        assert not in_progress.is_ended
        assert not canceling.is_ended


class TestBatchResultsBundle:
    """The bundle keeps successes and failures in parallel maps."""

    def test_total_counts_both_maps(self) -> None:
        bundle = BatchResultsBundle(
            successes={"a": _make_tool_use_result()},
            failures={
                "b": BatchError(custom_id="b", result_type="errored"),
                "c": BatchError(custom_id="c", result_type="expired"),
            },
        )
        assert bundle.total == 3

    def test_default_constructor_yields_empty_maps(self) -> None:
        bundle = BatchResultsBundle()
        assert bundle.successes == {}
        assert bundle.failures == {}
        assert bundle.total == 0


class TestDataclassBasics:
    """Smoke checks on the request/submission dataclasses."""

    def test_tool_use_batch_request_holds_all_fields(self) -> None:
        req = ToolUseBatchRequest(
            custom_id="subagent:a",
            prompt="hello",
            system_blocks=[{"type": "text", "text": "S"}],
            tool_schema={"name": "t"},
        )
        assert req.custom_id == "subagent:a"
        assert req.prompt == "hello"
        assert req.system_blocks[0]["type"] == "text"
        assert req.tool_schema["name"] == "t"

    def test_batch_submission_preserves_custom_id_order(self) -> None:
        sub = BatchSubmission(
            batch_id="msgbatch_x",
            custom_ids=["a", "b", "c"],
            submitted_at="2026-05-09T00:00:00+00:00",
        )
        assert sub.custom_ids == ["a", "b", "c"]


def _make_tool_use_result() -> ToolUseResult:
    """Tiny test double — saves wiring 6 fields per assertion."""
    return ToolUseResult(
        tool_name="report_tuning",
        tool_input={"tuned_content": "X", "changes": []},
        token_usage=TokenUsage(input_tokens=1, output_tokens=1),
        model="claude",
        message_id="msg_x",
    )
