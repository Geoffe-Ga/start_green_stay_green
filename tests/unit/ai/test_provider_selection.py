"""Unit tests for provider/model selection (tracer T2, #383).

Pins three contracts the selection layer must satisfy:

* **Precedence** — CLI flag > env (``GREEN_LLM_PROVIDER`` /
  ``GREEN_LLM_MODEL``) > config-file key > built-in default
  (Anthropic + :data:`DEFAULT_MODEL`). Each lower tier only wins when
  every higher tier is unset.
* **Normalization / validation** — provider names are normalized
  (case-folded, trimmed) and unknown providers raise a clear
  ``ValueError`` naming the supported set, never silently falling
  back.
* **Optional extra** — building the Anthropic provider succeeds when
  the SDK is importable, and surfaces a
  :class:`ProviderUnavailableError` with an actionable
  ``pip install`` hint (not a raw ``ImportError``) when the extra is
  absent.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

import pytest

from start_green_stay_green.ai.orchestrator import ModelConfig
from start_green_stay_green.ai.provider_selection import DEFAULT_MODEL
from start_green_stay_green.ai.provider_selection import DEFAULT_PROVIDER
from start_green_stay_green.ai.provider_selection import ProviderSelection
from start_green_stay_green.ai.provider_selection import ProviderUnavailableError
from start_green_stay_green.ai.provider_selection import _coalesce
from start_green_stay_green.ai.provider_selection import build_provider
from start_green_stay_green.ai.provider_selection import resolve_api_key_env_var
from start_green_stay_green.ai.provider_selection import resolve_provider_selection
from start_green_stay_green.ai.providers.base import LLMProvider

if TYPE_CHECKING:
    from collections.abc import Callable


# ----------------------------- precedence ---------------------------------
def test_default_selection_matches_today() -> None:
    """No flag / env / config → Anthropic + the current default model."""
    selection = resolve_provider_selection(
        provider_flag=None,
        model_flag=None,
        config={},
        env={},
    )
    assert selection == ProviderSelection(
        provider=DEFAULT_PROVIDER,
        model=DEFAULT_MODEL,
    )
    # The default model must be byte-for-byte today's hardcoded SONNET id
    # so existing behavior is unchanged.
    assert DEFAULT_MODEL == ModelConfig.SONNET
    assert DEFAULT_PROVIDER == "anthropic"


def test_cli_flag_beats_env_and_config() -> None:
    """CLI flag wins over both env and config for provider and model."""
    selection = resolve_provider_selection(
        provider_flag="anthropic",
        model_flag="model-from-flag",
        config={"llm_provider": "config-provider", "llm_model": "config-model"},
        env={
            "GREEN_LLM_PROVIDER": "env-provider",
            "GREEN_LLM_MODEL": "env-model",
        },
    )
    assert selection.provider == "anthropic"
    assert selection.model == "model-from-flag"


def test_env_beats_config() -> None:
    """Env var wins over config file when no CLI flag is given."""
    selection = resolve_provider_selection(
        provider_flag=None,
        model_flag=None,
        config={"llm_provider": "anthropic", "llm_model": "config-model"},
        env={"GREEN_LLM_MODEL": "env-model"},
    )
    assert selection.model == "env-model"


def test_config_beats_default() -> None:
    """Config-file key wins over the built-in default."""
    selection = resolve_provider_selection(
        provider_flag=None,
        model_flag=None,
        config={"llm_model": "config-model"},
        env={},
    )
    assert selection.model == "config-model"
    assert selection.provider == DEFAULT_PROVIDER


def test_per_field_precedence_is_independent() -> None:
    """Provider and model resolve independently across tiers."""
    selection = resolve_provider_selection(
        provider_flag=None,
        model_flag="model-flag",
        config={"llm_provider": "anthropic"},
        env={},
    )
    assert selection.provider == "anthropic"
    assert selection.model == "model-flag"


# --------------------------- normalization --------------------------------
@pytest.mark.parametrize("raw", ["Anthropic", "  anthropic  ", "ANTHROPIC"])
def test_provider_name_is_normalized(raw: str) -> None:
    """Provider names are case-folded and trimmed before lookup."""
    selection = resolve_provider_selection(
        provider_flag=raw,
        model_flag=None,
        config={},
        env={},
    )
    assert selection.provider == "anthropic"


def test_unknown_provider_raises_with_supported_set() -> None:
    """An unknown provider fails loudly and names the supported set."""
    with pytest.raises(ValueError, match="Unknown LLM provider") as exc:
        resolve_provider_selection(
            provider_flag="openai",
            model_flag=None,
            config={},
            env={},
        )
    assert "anthropic" in str(exc.value)


def test_blank_provider_falls_through_to_next_tier() -> None:
    """A whitespace-only flag is treated as unset, not as an error."""
    selection = resolve_provider_selection(
        provider_flag="   ",
        model_flag=None,
        config={"llm_provider": "anthropic"},
        env={},
    )
    assert selection.provider == "anthropic"


def test_blank_model_falls_through_to_default() -> None:
    """A whitespace-only model flag falls through to the default."""
    selection = resolve_provider_selection(
        provider_flag=None,
        model_flag="  ",
        config={},
        env={},
    )
    assert selection.model == DEFAULT_MODEL


def test_coalesce_returns_none_when_all_candidates_blank() -> None:
    """All-blank inputs collapse to ``None`` (the no-default fallthrough)."""
    assert _coalesce(None, "", "   ") is None


# ----------------------- model-id case preservation -----------------------
def test_model_flag_preserves_mixed_case() -> None:
    """A ``--model`` value keeps its exact case (model ids are case-sensitive)."""
    selection = resolve_provider_selection(
        provider_flag=None,
        model_flag="Claude-Sonnet-MixedCase",
        config={},
        env={},
    )
    assert selection.model == "Claude-Sonnet-MixedCase"


def test_env_model_preserves_mixed_case() -> None:
    """``GREEN_LLM_MODEL`` keeps its exact case through resolution."""
    selection = resolve_provider_selection(
        provider_flag=None,
        model_flag=None,
        config={},
        env={"GREEN_LLM_MODEL": "GPT-4o-Env"},
    )
    assert selection.model == "GPT-4o-Env"


def test_config_model_preserves_mixed_case() -> None:
    """A config ``llm_model`` value keeps its exact case through resolution."""
    selection = resolve_provider_selection(
        provider_flag=None,
        model_flag=None,
        config={"llm_model": "Config-Model-CamelCase"},
        env={},
    )
    assert selection.model == "Config-Model-CamelCase"


def test_model_flag_is_trimmed_but_not_folded() -> None:
    """Surrounding whitespace is stripped from the model, but case is kept."""
    selection = resolve_provider_selection(
        provider_flag=None,
        model_flag="  Foo-Bar  ",
        config={},
        env={},
    )
    assert selection.model == "Foo-Bar"


@pytest.mark.parametrize(
    ("provider_flag", "config", "env"),
    [
        ("ANTHROPIC", {}, {}),
        (None, {"llm_provider": "ANTHROPIC"}, {}),
        (None, {}, {"GREEN_LLM_PROVIDER": "ANTHROPIC"}),
    ],
)
def test_provider_remains_case_insensitive_across_tiers(
    provider_flag: str | None,
    config: dict[str, str],
    env: dict[str, str],
) -> None:
    """Provider names stay case-insensitive (registry keys) at every tier."""
    selection = resolve_provider_selection(
        provider_flag=provider_flag,
        model_flag=None,
        config=config,
        env=env,
    )
    assert selection.provider == "anthropic"


# --------------------------- api-key env var ------------------------------
def test_anthropic_api_key_env_var_is_unchanged() -> None:
    """The Anthropic provider still reads ``ANTHROPIC_API_KEY``."""
    assert resolve_api_key_env_var("anthropic") == "ANTHROPIC_API_KEY"


def test_api_key_env_var_normalizes_provider() -> None:
    """Provider name is normalized before env-var lookup."""
    assert resolve_api_key_env_var("  Anthropic ") == "ANTHROPIC_API_KEY"


def test_api_key_env_var_unknown_provider_raises() -> None:
    """An unknown provider has no key env var and raises."""
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        resolve_api_key_env_var("nope")


# ----------------------------- build_provider -----------------------------
def test_build_provider_returns_anthropic_instance() -> None:
    """``build_provider`` constructs a real provider when SDK present."""
    provider = build_provider(
        "anthropic",
        api_key="sk-test",  # pragma: allowlist secret
        model=DEFAULT_MODEL,
        max_retries=2,
        retry_delay=0.5,
    )
    assert isinstance(provider, LLMProvider)
    assert provider.model == DEFAULT_MODEL


def test_build_provider_unknown_raises() -> None:
    """Building an unknown provider raises a clear ValueError."""
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        build_provider("openai", api_key="x", model="m")


def _block_anthropic_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Make resolving the ``anthropic`` SDK raise ``ModuleNotFoundError``.

    Simulates the optional extra being absent without uninstalling it
    from the test environment. The provider's lazy seam resolves the
    SDK through :func:`importlib.import_module`, so patching that to
    reject ``anthropic`` (while leaving every other module importable)
    faithfully reproduces a missing extra.
    """
    real_import_module: Callable[..., object] = importlib.import_module

    def _fake_import_module(name: str, *args: object, **kwargs: object) -> object:
        if name == "anthropic" or name.startswith("anthropic."):
            msg = "No module named 'anthropic'"
            raise ModuleNotFoundError(msg)
        return real_import_module(name, *args, **kwargs)

    # The provider seam resolves the SDK via ``importlib.import_module``;
    # patch that exact symbol so only ``anthropic`` is blocked.
    monkeypatch.setattr(importlib, "import_module", _fake_import_module)


def test_build_provider_succeeds_without_touching_sdk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Constructing a provider never imports the SDK (cheap + I/O-free).

    The optional extra is only needed once a generation method runs, so
    ``build_provider`` must succeed even when the SDK is absent — this is
    what keeps ``import start_green_stay_green`` / ``green --help``
    working without the extra.
    """
    _block_anthropic_import(monkeypatch)
    provider = build_provider("anthropic", api_key="x", model="m")
    assert provider.model == "m"


def test_missing_extra_raises_actionable_error_on_use(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Using a provider whose extra is absent yields an install hint."""
    _block_anthropic_import(monkeypatch)
    provider = build_provider("anthropic", api_key="x", model="m")

    with pytest.raises(ProviderUnavailableError) as exc:
        provider.generate("hello", "yaml")

    message = str(exc.value)
    assert "pip install" in message
    assert "anthropic" in message
    # The original ImportError must be chained, not swallowed.
    assert isinstance(exc.value.__cause__, ImportError)


def test_provider_unavailable_is_importerror_subclass() -> None:
    """Callers catching ImportError still catch the friendlier error."""
    assert issubclass(ProviderUnavailableError, ImportError)
