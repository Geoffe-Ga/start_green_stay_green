"""Unit tests for the batch primitives in ``ai/batch.py``.

The orchestrator's batch methods are integration concerns covered
elsewhere; this file pins the pure-data parser
(:func:`parse_batch_result_entry`) and the dataclass shapes against
both real-SDK-shaped payloads (Pydantic-style attribute access) and
plain-dict test doubles.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from dataclasses import dataclass
from typing import Any

import pytest

from start_green_stay_green.ai.batch import BatchError
from start_green_stay_green.ai.batch import BatchPoll
from start_green_stay_green.ai.batch import BatchResultsBundle
from start_green_stay_green.ai.batch import BatchSubmission
from start_green_stay_green.ai.batch import ToolUseBatchRequest
from start_green_stay_green.ai.batch import _iter_blocks
from start_green_stay_green.ai.batch import parse_batch_result_entry
from start_green_stay_green.ai.types import GenerationError
from start_green_stay_green.ai.types import TokenUsage
from start_green_stay_green.ai.types import ToolUseResult

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
    usage: dict[str, object] | None = None,
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
                "usage": usage if usage is not None else _DEFAULT_USAGE.copy(),
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

    def test_model_and_message_id_are_lifted_exactly(self) -> None:
        """Pin ``model``/``id`` keys flow through non-empty (not coerced)."""
        _, outcome = parse_batch_result_entry(_success_entry())
        assert isinstance(outcome, ToolUseResult)
        assert outcome.model == "claude-sonnet"
        assert outcome.message_id == "msg_123"

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
        assert outcome.message == f"upstream {failure_type}"

    def test_unknown_result_type_is_recorded_as_batcherror(self) -> None:
        entry = {
            "custom_id": "subagent:weird",
            "result": {"type": "future_status_we_havent_heard_of"},
        }

        _, outcome = parse_batch_result_entry(entry)
        assert isinstance(outcome, BatchError)
        assert outcome.result_type == "future_status_we_havent_heard_of"

    def test_missing_result_type_attribute_yields_unknown_batcherror(self) -> None:
        """A ``result`` payload with no ``type`` field at all degrades soft.

        Pins the contract: a SDK shape change that drops ``result.type``
        produces a recoverable ``BatchError`` (caller can decide), not
        a ``GenerationError`` that aborts the whole batch reconciliation.
        """
        entry = {
            "custom_id": "subagent:no_type",
            "result": {"message": {"content": []}},  # no "type" key
        }

        custom_id, outcome = parse_batch_result_entry(entry)
        assert custom_id == "subagent:no_type"
        assert isinstance(outcome, BatchError)
        assert outcome.result_type == "unknown"
        assert outcome.message == "Batch result entry is missing result.type"

    def test_missing_custom_id_raises_generation_error(self) -> None:
        with pytest.raises(GenerationError, match="custom_id") as exc:
            parse_batch_result_entry({"custom_id": "", "result": {}})
        assert str(exc.value).startswith(
            "Batch result entry is missing a usable custom_id"
        )

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
        with pytest.raises(GenerationError, match="ToolUseBlock") as exc:
            parse_batch_result_entry(entry)
        assert str(exc.value).startswith(
            "Batch result message did not contain a ToolUseBlock"
        )

    def test_non_dict_tool_input_raises(self) -> None:
        entry = _success_entry()
        entry["result"]["message"]["content"][0]["input"] = "not-a-dict"
        with pytest.raises(GenerationError, match="JSON object") as exc:
            parse_batch_result_entry(entry)
        assert str(exc.value).startswith(
            "Batch ToolUseBlock.input was not a JSON object"
        )


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
        assert not bundle.successes
        assert not bundle.failures
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


class TestFalsyFieldCoercion:
    """Missing/empty success fields coerce to ``""``, not a placeholder."""

    def test_missing_tool_name_coerces_to_empty_string(self) -> None:
        entry = _success_entry()
        del entry["result"]["message"]["content"][0]["name"]
        _, outcome = parse_batch_result_entry(entry)
        assert isinstance(outcome, ToolUseResult)
        assert outcome.tool_name == ""

    def test_missing_model_coerces_to_empty_string(self) -> None:
        entry = _success_entry()
        del entry["result"]["message"]["model"]
        _, outcome = parse_batch_result_entry(entry)
        assert isinstance(outcome, ToolUseResult)
        assert outcome.model == ""

    def test_missing_message_id_coerces_to_empty_string(self) -> None:
        entry = _success_entry()
        del entry["result"]["message"]["id"]
        _, outcome = parse_batch_result_entry(entry)
        assert isinstance(outcome, ToolUseResult)
        assert outcome.message_id == ""


class TestErrorMessageLift:
    """``_extract_error_message`` reads the ``message`` key precisely."""

    def test_missing_error_payload_yields_empty_message(self) -> None:
        entry = {"custom_id": "x", "result": {"type": "errored"}}
        _, outcome = parse_batch_result_entry(entry)
        assert isinstance(outcome, BatchError)
        assert outcome.message == ""

    def test_message_read_from_message_key_not_stringified_error(self) -> None:
        """The ``message`` key wins over ``str(error)`` of the whole dict."""
        entry = {
            "custom_id": "x",
            "result": {
                "type": "errored",
                "error": {"type": "overloaded", "message": "real reason"},
            },
        }
        _, outcome = parse_batch_result_entry(entry)
        assert isinstance(outcome, BatchError)
        assert outcome.message == "real reason"

    def test_non_string_message_falls_back_to_stringified_error(self) -> None:
        entry = {
            "custom_id": "x",
            "result": {"type": "errored", "error": {"message": 42}},
        }
        _, outcome = parse_batch_result_entry(entry)
        assert isinstance(outcome, BatchError)
        assert outcome.message == "{'message': 42}"


class TestIntAttr:
    """``_int_attr`` parses ints/numeric strings and defaults to ``0``."""

    def test_non_numeric_string_usage_defaults_to_zero(self) -> None:
        """A non-digit string must not be coerced — guards ``and`` vs ``or``."""
        usage: dict[str, object] = {"input_tokens": "abc", "output_tokens": 9}
        entry = _success_entry(usage=usage)
        _, outcome = parse_batch_result_entry(entry)
        assert isinstance(outcome, ToolUseResult)
        assert outcome.token_usage.input_tokens == 0
        assert outcome.token_usage.output_tokens == 9

    def test_absent_usage_field_defaults_to_zero(self) -> None:
        entry = _success_entry(usage={"input_tokens": 4})
        _, outcome = parse_batch_result_entry(entry)
        assert isinstance(outcome, ToolUseResult)
        assert outcome.token_usage.output_tokens == 0
        assert outcome.cache_read_tokens == 0
        assert outcome.cache_creation_tokens == 0


class TestIterBlocks:
    """``_iter_blocks`` normalizes None/single/list content payloads."""

    def test_none_content_yields_empty_iterable(self) -> None:
        """``None`` becomes an empty list, not ``[None]`` (kills is-not-None)."""
        assert not list(_iter_blocks(None))

    def test_single_block_wraps_in_list(self) -> None:
        block = {"type": "tool_use"}
        assert list(_iter_blocks(block)) == [block]

    def test_list_content_passes_through(self) -> None:
        blocks = [{"type": "text"}, {"type": "tool_use"}]
        assert list(_iter_blocks(blocks)) == blocks


class TestDataclassImmutability:
    """All five batch dataclasses are frozen (hashable, no mutation)."""

    def test_tool_use_batch_request_is_frozen(self) -> None:
        req = ToolUseBatchRequest(
            custom_id="a", prompt="p", system_blocks=[], tool_schema={}
        )
        with pytest.raises(FrozenInstanceError, match="custom_id"):
            req.custom_id = "b"  # type: ignore[misc]

    def test_batch_submission_is_frozen(self) -> None:
        sub = BatchSubmission(batch_id="b", custom_ids=[], submitted_at="t")
        with pytest.raises(FrozenInstanceError, match="batch_id"):
            sub.batch_id = "c"  # type: ignore[misc]

    def test_batch_poll_is_frozen(self) -> None:
        poll = BatchPoll(
            batch_id="b",
            status="ended",
            processing_count=0,
            succeeded_count=0,
            errored_count=0,
        )
        with pytest.raises(FrozenInstanceError, match="status"):
            poll.status = "in_progress"  # type: ignore[misc]

    def test_batch_error_is_frozen(self) -> None:
        err = BatchError(custom_id="x", result_type="errored")
        with pytest.raises(FrozenInstanceError, match="message"):
            err.message = "changed"  # type: ignore[misc]

    def test_batch_results_bundle_is_frozen(self) -> None:
        bundle = BatchResultsBundle()
        with pytest.raises(FrozenInstanceError, match="successes"):
            bundle.successes = {}  # type: ignore[misc]


class TestDataclassDefaults:
    """Optional count/message fields default to their documented values."""

    def test_batch_poll_count_defaults_are_zero(self) -> None:
        poll = BatchPoll(
            batch_id="b",
            status="ended",
            processing_count=0,
            succeeded_count=0,
            errored_count=0,
        )
        assert poll.canceled_count == 0
        assert poll.expired_count == 0

    def test_batch_error_message_defaults_to_empty_string(self) -> None:
        err = BatchError(custom_id="x", result_type="errored")
        assert err.message == ""


def _make_tool_use_result() -> ToolUseResult:
    """Tiny test double — saves wiring 6 fields per assertion."""
    return ToolUseResult(
        tool_name="report_tuning",
        tool_input={"tuned_content": "X", "changes": []},
        token_usage=TokenUsage(input_tokens=1, output_tokens=1),
        model="claude",
        message_id="msg_x",
    )
