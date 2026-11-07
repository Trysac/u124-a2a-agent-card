"""Behavior tests for the public API of a2a_agent_card."""

from __future__ import annotations

import pytest

import a2a_agent_card


def test_normalize_trims_and_lowercases() -> None:
    assert a2a_agent_card.normalize("  Hello World ") == "hello world"


@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_normalize_rejects_blank_input(value: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        a2a_agent_card.normalize(value)


def test_version_is_semver() -> None:
    parts = a2a_agent_card.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
