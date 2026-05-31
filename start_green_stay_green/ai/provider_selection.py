"""Provider/model selection for the AI subsystem (tracer T2, #383).

Turns the :class:`~start_green_stay_green.ai.providers.base.LLMProvider`
seam from tracer T1 (#381) into a *selectable* backend. Three things
live here, all provider-neutral:

* **Resolution** — :func:`resolve_provider_selection` collapses the
  four configuration tiers into a single :class:`ProviderSelection`
  with documented precedence: **CLI flag > env var
  (``GREEN_LLM_PROVIDER`` / ``GREEN_LLM_MODEL``) > config-file key >
  built-in default** (Anthropic + the current model id). The default
  is byte-for-byte today's behavior, so callers that pass nothing are
  unchanged.
* **Construction** — :func:`build_provider` lazily imports the
  selected provider's module so the heavy vendor SDK can be an
  optional install extra. A missing extra is reported as a
  :class:`ProviderUnavailableError` carrying an actionable
  ``pip install`` hint rather than a raw :class:`ImportError`.
* **Auth** — :func:`resolve_api_key_env_var` maps a provider to the
  environment variable its key is read from, keeping
  ``ANTHROPIC_API_KEY`` working untouched.

No provider names, model ids, or env-var keys are logged here; the
caller owns secret handling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final
from typing import Protocol
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

    from start_green_stay_green.ai.providers.base import LLMProvider


class _ProviderFactory(Protocol):
    """Constructor contract shared by every concrete provider class.

    Every provider in the registry is built with the same keyword
    arguments (``api_key`` plus retry/model policy), so typing the
    lazily-imported class as this protocol lets :func:`build_provider`
    call it without mypy losing the concrete ``__init__`` signature to
    the abstract :class:`LLMProvider` base.
    """

    def __call__(
        self,
        api_key: str,
        *,
        model: str,
        max_retries: int = ...,
        retry_delay: float = ...,
    ) -> LLMProvider:
        """Construct a provider; see ``AnthropicProvider.__init__``."""
        ...  # pragma: no cover - structural typing only


__all__ = [
    "DEFAULT_MODEL",
    "DEFAULT_PROVIDER",
    "ENV_MODEL",
    "ENV_PROVIDER",
    "ProviderSelection",
    "ProviderUnavailableError",
    "build_provider",
    "resolve_api_key_env_var",
    "resolve_provider_selection",
    "supported_providers",
]

# Built-in default model id. Mirrors the value tracer T1 hardcoded on
# ``ModelConfig.SONNET`` so the no-flags / no-env / no-config path is
# identical to today's behavior. Duplicated here as a literal (rather
# than importing ``ModelConfig``) to keep this selection layer free of
# any dependency on the orchestrator; the equality is pinned by a test.
DEFAULT_MODEL: Final[str] = "claude-sonnet-4-5-20250929"

# Built-in default provider. Anthropic remains the zero-config default.
DEFAULT_PROVIDER: Final[str] = "anthropic"

# Environment variables for the selection layer. Documented precedence
# tier 2 (below CLI flags, above config-file keys).
ENV_PROVIDER: Final[str] = "GREEN_LLM_PROVIDER"
ENV_MODEL: Final[str] = "GREEN_LLM_MODEL"

# Config-file keys read for tier 3.
_CONFIG_PROVIDER_KEY: Final[str] = "llm_provider"
_CONFIG_MODEL_KEY: Final[str] = "llm_model"


@dataclass(frozen=True)
class ProviderSpec:
    """Static metadata describing a selectable provider.

    Attributes:
        module: Dotted path of the module hosting the concrete
            :class:`LLMProvider`. Imported lazily so the vendor SDK
            can be an optional extra.
        class_name: Name of the provider class within ``module``.
        api_key_env_var: Environment variable the provider's API key
            is read from (kept stable for backward compatibility).
    """

    module: str
    class_name: str
    api_key_env_var: str


# Registry of every selectable provider. Tracer T2 ships only the
# Anthropic entry (T3, #385, adds the second concrete provider). Keying
# by the normalized provider name keeps lookup, validation, and the
# "supported set" error message all driven by one source of truth.
_PROVIDERS: Final[dict[str, ProviderSpec]] = {
    "anthropic": ProviderSpec(
        module="start_green_stay_green.ai.providers.anthropic_provider",
        class_name="AnthropicProvider",
        api_key_env_var="ANTHROPIC_API_KEY",  # pragma: allowlist secret
    ),
}


class ProviderUnavailableError(ImportError):
    """A selected provider's optional dependency is not installed.

    Subclasses :class:`ImportError` so existing ``except ImportError``
    handlers keep working, while the message adds an actionable
    ``pip install ...[extra]`` hint instead of a bare
    "No module named ...". The triggering :class:`ImportError` is
    chained as ``__cause__``.
    """


@dataclass(frozen=True)
class ProviderSelection:
    """Resolved provider + model after applying precedence.

    Attributes:
        provider: Normalized provider name (a key of the registry).
        model: Model identifier to generate with.
    """

    provider: str
    model: str


def supported_providers() -> tuple[str, ...]:
    """Return the sorted tuple of registered provider names.

    Returns:
        Provider names in stable alphabetical order, suitable for
        help text and error messages.
    """
    return tuple(sorted(_PROVIDERS))


def _normalize(value: str | None) -> str | None:
    """Trim and case-fold ``value``; treat blank/``None`` as unset.

    Returns:
        The normalized non-empty string, or ``None`` when ``value`` is
        ``None`` or only whitespace (so the next precedence tier wins).
    """
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed.casefold() if trimmed else None


def _coalesce(*candidates: str | None) -> str | None:
    """Return the first normalized, non-blank candidate, or ``None``.

    Args:
        *candidates: Values in descending precedence order.

    Returns:
        The first candidate that is not ``None`` after normalization.
    """
    for candidate in candidates:
        normalized = _normalize(candidate)
        if normalized is not None:
            return normalized
    return None


def _coalesce_with_default(default: str, *candidates: str | None) -> str:
    """Coalesce ``candidates`` then fall back to a guaranteed ``default``.

    Args:
        default: Non-blank fallback used when every candidate is unset.
            Module-level constants (:data:`DEFAULT_PROVIDER`,
            :data:`DEFAULT_MODEL`) supply this, so the result is always
            a concrete ``str`` — no ``None`` and therefore no defensive
            ``assert`` at the call site.
        *candidates: Higher-precedence values in descending order.

    Returns:
        The first non-blank candidate, or the ``default`` (normalized).
    """
    return _coalesce(*candidates, default) or default


def _require_known(provider: str) -> str:
    """Validate ``provider`` is registered; return it unchanged.

    Args:
        provider: An already-normalized provider name.

    Returns:
        The same name when it is a registry key.

    Raises:
        ValueError: If the provider is not registered. The message
            names the supported set so the user can self-correct.
    """
    if provider not in _PROVIDERS:
        supported = ", ".join(supported_providers())
        msg = f"Unknown LLM provider {provider!r}. Supported providers: {supported}."
        raise ValueError(msg)
    return provider


def resolve_provider_selection(
    *,
    provider_flag: str | None,
    model_flag: str | None,
    config: Mapping[str, str],
    env: Mapping[str, str],
) -> ProviderSelection:
    """Collapse the four config tiers into one :class:`ProviderSelection`.

    Precedence (highest first), resolved independently per field:

    1. CLI flag (``provider_flag`` / ``model_flag``)
    2. Environment (``GREEN_LLM_PROVIDER`` / ``GREEN_LLM_MODEL``)
    3. Config-file keys (``llm_provider`` / ``llm_model``)
    4. Built-in default (:data:`DEFAULT_PROVIDER` / :data:`DEFAULT_MODEL`)

    Blank / whitespace-only values at any tier are treated as unset, so
    they fall through to the next tier rather than erroring.

    Args:
        provider_flag: Value of the ``--provider`` CLI flag, or ``None``.
        model_flag: Value of the ``--model`` CLI flag, or ``None``.
        config: Parsed config-file mapping (may be empty).
        env: Environment mapping to read selection vars from (pass
            ``os.environ`` in production; an explicit mapping keeps the
            resolver pure and testable).

    Returns:
        The resolved :class:`ProviderSelection`.

    Raises:
        ValueError: If the resolved provider is not registered.
    """
    provider = _coalesce_with_default(
        DEFAULT_PROVIDER,
        provider_flag,
        env.get(ENV_PROVIDER),
        config.get(_CONFIG_PROVIDER_KEY),
    )
    model = _coalesce_with_default(
        DEFAULT_MODEL,
        model_flag,
        env.get(ENV_MODEL),
        config.get(_CONFIG_MODEL_KEY),
    )
    return ProviderSelection(provider=_require_known(provider), model=model)


def resolve_api_key_env_var(provider: str) -> str:
    """Return the env var holding ``provider``'s API key.

    Args:
        provider: Provider name (normalized internally).

    Returns:
        The environment-variable name (for Anthropic,
        ``ANTHROPIC_API_KEY`` — unchanged from before T2).

    Raises:
        ValueError: If the provider is not registered.
    """
    normalized = _normalize(provider) or ""
    return _PROVIDERS[_require_known(normalized)].api_key_env_var


def build_provider(
    provider: str,
    *,
    api_key: str,
    model: str,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> LLMProvider:
    """Construct the concrete :class:`LLMProvider` for ``provider``.

    The provider's module is imported lazily so the vendor SDK can be
    an optional install extra: importing this selection module — and
    therefore ``import start_green_stay_green`` and ``green --help`` —
    never requires any provider SDK.

    Args:
        provider: Provider name (normalized internally).
        api_key: API key forwarded to the provider constructor.
        model: Model identifier to generate with.
        max_retries: Maximum retry attempts. Defaults to 3.
        retry_delay: Initial retry delay in seconds. Defaults to 1.0.

    Constructing the provider is cheap and performs no I/O or SDK
    import: the vendor SDK is only loaded when a generation method
    runs, at which point a missing extra is reported as a
    :class:`ProviderUnavailableError` by the provider itself. This is
    what lets ``import start_green_stay_green`` and ``green --help``
    work without the extra installed.

    Returns:
        A constructed provider satisfying the :class:`LLMProvider`
        contract.

    Raises:
        ValueError: If the provider is not registered.
    """
    normalized = _normalize(provider) or ""
    spec = _PROVIDERS[_require_known(normalized)]
    provider_cls = _load_provider_class(spec)
    return provider_cls(
        api_key,
        model=model,
        max_retries=max_retries,
        retry_delay=retry_delay,
    )


def _load_provider_class(spec: ProviderSpec) -> _ProviderFactory:
    """Import and return the provider class named by ``spec``.

    The provider *module* is import-clean (it imports its vendor SDK
    lazily), so importing it here does not require the optional extra.
    The extra is only needed when a provider method runs.

    Args:
        spec: Registry entry describing where the class lives.

    Returns:
        The provider class, typed as the shared
        :class:`_ProviderFactory` constructor protocol.
    """
    from importlib import (  # noqa: PLC0415 — keep import-time cost off the hot path
        import_module,
    )

    module = import_module(spec.module)
    provider_cls: _ProviderFactory = getattr(module, spec.class_name)
    return provider_cls
