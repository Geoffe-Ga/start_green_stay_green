"""YAML merge utility for .pre-commit-config.yaml files.

Provides intelligent merging of pre-commit configurations: keeps existing
repos and their settings, appends new repos from the generated config,
and preserves top-level keys from both sources.
"""

from __future__ import annotations

from typing import Any

import yaml


def merge_precommit_configs(
    existing_yaml: str,
    generated_yaml: str,
) -> tuple[str, int, int]:
    """Merge generated pre-commit config into an existing one.

    Merge strategy:
    - Repos with the same URL: keep existing config entirely
    - New repos not in existing: append to repos list
    - Top-level keys: keep existing values, add missing from generated

    Args:
        existing_yaml: Contents of the existing .pre-commit-config.yaml.
            Empty string is treated as no existing config.
        generated_yaml: Contents of the newly generated config.

    Returns:
        Tuple of (merged_yaml, added_count, kept_count) where:
        - merged_yaml: The merged YAML string
        - added_count: Number of new repos appended
        - kept_count: Number of existing repos preserved

    Raises:
        ValueError: If either YAML string is malformed.
    """
    if not existing_yaml.strip():
        return _handle_empty_existing(generated_yaml)

    existing = _safe_parse(existing_yaml)
    generated = _safe_parse(generated_yaml)

    merged_repos, added_count, kept_count = _merge_repos(existing, generated)

    merged = _merge_top_level_keys(existing, generated)
    merged["repos"] = merged_repos

    merged_yaml = yaml.dump(merged, default_flow_style=False, sort_keys=False)
    return merged_yaml, added_count, kept_count


def _handle_empty_existing(generated_yaml: str) -> tuple[str, int, int]:
    """Handle case where existing config is empty.

    Args:
        generated_yaml: Generated YAML to use as-is.

    Returns:
        Tuple of (yaml, added_count, kept_count=0).
    """
    generated = _safe_parse(generated_yaml)
    generated_repos = generated.get("repos") or []
    return generated_yaml, len(generated_repos), 0


def _merge_repos(
    existing: dict[str, Any],
    generated: dict[str, Any],
) -> tuple[list[dict[str, Any]], int, int]:
    """Merge repo lists, keeping existing and appending new.

    Args:
        existing: Parsed existing config.
        generated: Parsed generated config.

    Returns:
        Tuple of (merged_repos, added_count, kept_count).
    """
    existing_repos = _get_repos(existing)
    generated_repos = _get_repos(generated)

    existing_urls = {repo["repo"] for repo in existing_repos if "repo" in repo}
    new_repos = [
        repo for repo in generated_repos if repo.get("repo") not in existing_urls
    ]

    return [*existing_repos, *new_repos], len(new_repos), len(existing_repos)


def _get_repos(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract repos list from config, defaulting to empty list.

    Args:
        config: Parsed YAML config.

    Returns:
        List of repo dictionaries.
    """
    repos = config.get("repos")
    return repos if isinstance(repos, list) else []


def _safe_parse(yaml_str: str) -> dict[str, Any]:
    """Parse YAML string safely, raising ValueError on failure.

    Args:
        yaml_str: YAML string to parse.

    Returns:
        Parsed dictionary.

    Raises:
        ValueError: If YAML is malformed.
        TypeError: If YAML is not a mapping.
    """
    try:
        result = yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        msg = f"Invalid YAML: {e}"
        raise ValueError(msg) from e

    if result is None:
        return {}
    if not isinstance(result, dict):
        msg = (
            f"Invalid pre-commit config: expected mapping, got {type(result).__name__}"
        )
        raise TypeError(msg)
    return result


def _merge_top_level_keys(
    existing: dict[str, Any],
    generated: dict[str, Any],
) -> dict[str, Any]:
    """Merge top-level keys, preferring existing values.

    Args:
        existing: Parsed existing config.
        generated: Parsed generated config.

    Returns:
        Merged dictionary with existing values preferred.
    """
    merged: dict[str, Any] = {}
    all_keys = list(existing.keys())
    for key in generated:
        if key not in all_keys:
            all_keys.append(key)

    for key in all_keys:
        if key != "repos":
            merged[key] = existing.get(key, generated.get(key))

    return merged
