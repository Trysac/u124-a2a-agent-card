"""Unit tests for a2a_agent_card package."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from a2a_agent_card import (
    A2ACardError,
    Capabilities,
    Interface,
    Issue,
    Skill,
    build_card,
    validate_card,
    well_known_url,
)
from a2a_agent_card.__main__ import main


def test_acceptance_criteria_1() -> None:
    card = build_card(
        name="Search",
        description="Finds docs",
        version="1.0.0",
        interfaces=[Interface("https://agent.example.com/a2a", "JSONRPC", "1.0")],
        skills=[Skill("search", "Search", "Search docs", ("docs",))],
    )
    assert sorted(card.keys()) == [
        "capabilities",
        "defaultInputModes",
        "defaultOutputModes",
        "description",
        "name",
        "skills",
        "supportedInterfaces",
        "version",
    ]
    assert validate_card(card) == []


def test_acceptance_criteria_2() -> None:
    card = {
        "name": "Search",
        "description": "Finds docs",
        "version": "1.0.0",
        "supportedInterfaces": [
            {
                "url": "https://agent.example.com/a2a",
                "protocolBinding": "JSONRPC",
                "protocolVersion": "1.0",
            }
        ],
        "capabilities": {},
        "defaultInputModes": ["text/plain"],
        "defaultOutputModes": ["text/plain"],
    }
    issues = validate_card(card)
    assert Issue("skills", "missing", "error") in issues

    card_with_skill_without_tags = {
        "name": "Search",
        "description": "Finds docs",
        "version": "1.0.0",
        "supportedInterfaces": [
            {
                "url": "https://agent.example.com/a2a",
                "protocolBinding": "JSONRPC",
                "protocolVersion": "1.0",
            }
        ],
        "capabilities": {},
        "defaultInputModes": ["text/plain"],
        "defaultOutputModes": ["text/plain"],
        "skills": [{"id": "s1", "name": "S1", "description": "Desc"}],
    }
    skill_issues = validate_card(card_with_skill_without_tags)
    assert Issue("skills[0].tags", "missing", "error") in skill_issues


def test_acceptance_criteria_3() -> None:
    card = build_card(
        name="Search",
        description="Finds docs",
        version="1.0.0",
        interfaces=[Interface("https://agent.example.com/a2a", "JSONRPC", "1.0")],
        skills=[
            Skill("search", "Search 1", "Search docs 1", ("docs",)),
            Skill("search", "Search 2", "Search docs 2", ("docs",)),
        ],
    )
    issues = validate_card(card)
    assert Issue("skills[1].id", "duplicate_skill_id", "error") in issues


def test_acceptance_criteria_4() -> None:
    # ftp://x
    card_ftp = build_card(
        name="Search",
        description="Finds docs",
        version="1.0.0",
        interfaces=[Interface("ftp://x", "JSONRPC", "1.0")],
        skills=[Skill("s", "S", "D", ("t",))],
    )
    issues_ftp = validate_card(card_ftp)
    assert Issue("supportedInterfaces[0].url", "invalid_url", "error") in issues_ftp

    # http://example.com/a2a
    card_http = build_card(
        name="Search",
        description="Finds docs",
        version="1.0.0",
        interfaces=[Interface("http://example.com/a2a", "JSONRPC", "1.0")],
        skills=[Skill("s", "S", "D", ("t",))],
    )
    issues_http = validate_card(card_http)
    assert Issue("supportedInterfaces[0].url", "invalid_url", "error") in issues_http

    # http://localhost:8080/a2a is accepted
    card_local = build_card(
        name="Search",
        description="Finds docs",
        version="1.0.0",
        interfaces=[Interface("http://localhost:8080/a2a", "JSONRPC", "1.0")],
        skills=[Skill("s", "S", "D", ("t",))],
    )
    assert [i for i in validate_card(card_local) if i.path == "supportedInterfaces[0].url"] == []

    # protocolBinding 'SOAP'
    card_soap = build_card(
        name="Search",
        description="Finds docs",
        version="1.0.0",
        interfaces=[Interface("https://agent.example.com/a2a", "SOAP", "1.0")],
        skills=[Skill("s", "S", "D", ("t",))],
    )
    issues_soap = validate_card(card_soap)
    assert (
        Issue("supportedInterfaces[0].protocolBinding", "unknown_binding", "warning") in issues_soap
    )


def test_acceptance_criteria_5() -> None:
    card = {
        "name": "Search",
        "description": "Finds docs",
        "version": "1.0.0",
        "supportedInterfaces": [
            {
                "url": "https://agent.example.com/a2a",
                "protocolBinding": "JSONRPC",
                "protocolVersion": "1.0",
            }
        ],
        "capabilities": {"streaming": "yes"},
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["application/json"],
        "skills": [{"id": "s", "name": "S", "description": "D", "tags": ["t"]}],
        "foo": "bar",
    }
    issues = validate_card(card)
    assert Issue("defaultInputModes[0]", "invalid_media_type", "error") in issues
    assert Issue("foo", "unknown_field", "warning") in issues
    assert Issue("capabilities.streaming", "type", "error") in issues


def test_acceptance_criteria_6() -> None:
    assert (
        well_known_url("https://agent.example.com/base/")
        == "https://agent.example.com/.well-known/agent-card.json"
    )
    with pytest.raises(A2ACardError) as exc_info:
        well_known_url("agent.example.com")
    assert exc_info.value.code == "invalid_url"


def test_acceptance_criteria_7(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # 1. Duplicate skill id -> prints and returns 1
    dup_card = build_card(
        name="Search",
        description="Finds docs",
        version="1.0.0",
        interfaces=[Interface("https://agent.example.com/a2a", "JSONRPC", "1.0")],
        skills=[
            Skill("search", "Search 1", "Search docs 1", ("docs",)),
            Skill("search", "Search 2", "Search docs 2", ("docs",)),
        ],
    )
    f1 = tmp_path / "dup.json"
    f1.write_text(json.dumps(dup_card), encoding="utf-8")
    ret1 = main(["validate", str(f1)])
    captured1 = capsys.readouterr()
    assert ret1 == 1
    assert "error skills[1].id duplicate_skill_id" in captured1.out

    # 2. Valid card -> prints ok and returns 0
    valid_card = build_card(
        name="Search",
        description="Finds docs",
        version="1.0.0",
        interfaces=[Interface("https://agent.example.com/a2a", "JSONRPC", "1.0")],
        skills=[Skill("search", "Search", "Search docs", ("docs",))],
    )
    f2 = tmp_path / "valid.json"
    f2.write_text(json.dumps(valid_card), encoding="utf-8")
    ret2 = main(["validate", str(f2)])
    captured2 = capsys.readouterr()
    assert ret2 == 0
    assert captured2.out.strip() == "ok"

    # 3. Invalid JSON -> returns 2
    f3 = tmp_path / "invalid.json"
    f3.write_text("{not valid json", encoding="utf-8")
    ret3 = main(["validate", str(f3)])
    assert ret3 == 2

    # 4. File over 1_048_576 bytes -> returns 2
    f4 = tmp_path / "oversize.json"
    f4.write_text(" " * (1_048_576 + 1), encoding="utf-8")
    ret4 = main(["validate", str(f4)])
    assert ret4 == 2


def test_build_card_options_and_errors() -> None:
    # Missing skills raises A2ACardError invalid_input
    with pytest.raises(A2ACardError) as exc_info:
        build_card(
            name="Search",
            description="Finds docs",
            version="1.0.0",
            interfaces=[Interface("https://agent.example.com/a2a", "JSONRPC", "1.0")],
            skills=[],
        )
    assert exc_info.value.code == "invalid_input"

    # Missing interfaces
    with pytest.raises(A2ACardError) as exc_info2:
        build_card(
            name="Search",
            description="Finds docs",
            version="1.0.0",
            interfaces=[],
            skills=[Skill("search", "Search", "Search docs", ("docs",))],
        )
    assert exc_info2.value.code == "invalid_input"

    # Invalid name
    with pytest.raises(A2ACardError) as exc_info3:
        build_card(
            name=" ",
            description="Finds docs",
            version="1.0.0",
            interfaces=[Interface("https://agent.example.com/a2a", "JSONRPC", "1.0")],
            skills=[Skill("search", "Search", "Search docs", ("docs",))],
        )
    assert exc_info3.value.code == "invalid_input"

    # Full build with optional fields
    card = build_card(
        name="Full Agent",
        description="Full description",
        version="2.0.0",
        interfaces=[Interface("https://agent.example.com/a2a", "GRPC", "2.0", tenant="tenant-1")],
        skills=[
            Skill(
                id="s1",
                name="Skill 1",
                description="D1",
                tags=("tag1", "tag2"),
                examples=("Example 1",),
                input_modes=("application/json",),
                output_modes=("application/json",),
            )
        ],
        capabilities=Capabilities(
            streaming=True, push_notifications=False, extended_agent_card=True
        ),
        provider=("Example Org", "https://example.org"),
        documentation_url="https://docs.example.org",
        icon_url="https://example.org/icon.png",
    )
    assert card["capabilities"] == {
        "streaming": True,
        "pushNotifications": False,
        "extendedAgentCard": True,
    }
    assert card["provider"] == {"organization": "Example Org", "url": "https://example.org"}
    assert card["documentationUrl"] == "https://docs.example.org"
    assert card["iconUrl"] == "https://example.org/icon.png"
    assert card["supportedInterfaces"][0]["tenant"] == "tenant-1"
    assert card["skills"][0]["examples"] == ["Example 1"]
    assert validate_card(card) == []


def test_validate_card_edge_cases() -> None:
    # Card as list
    issues = validate_card([1, 2, 3])  # type: ignore[arg-type]
    assert issues == [Issue("", "type", "error")]

    # Empty skills list is valid per spec
    card = build_card(
        name="Search",
        description="Finds docs",
        version="1.0.0",
        interfaces=[Interface("https://agent.example.com/a2a", "JSONRPC", "1.0")],
        skills=[Skill("s", "S", "D", ("t",))],
    )
    card["skills"] = []
    assert validate_card(card) == []

    # Empty strings in required fields
    bad_card: dict[str, Any] = {
        "name": " ",
        "description": " ",
        "version": " ",
        "supportedInterfaces": [
            {
                "url": " ",
                "protocolBinding": " ",
                "protocolVersion": " ",
                "tenant": " ",
                "extra": 123,
            }
        ],
        "capabilities": {
            "pushNotifications": "not-bool",
            "extendedAgentCard": 1,
            "extensions": "not-a-list",
        },
        "defaultInputModes": [" "],
        "defaultOutputModes": [123],
        "skills": [
            {
                "id": " ",
                "name": " ",
                "description": " ",
                "tags": [" ", 123],
                "examples": [" ", 456],
                "inputModes": ["invalid-type-1"],
                "outputModes": ["invalid-type-2"],
                "securityRequirements": 123,
                "extra": "val",
            }
        ],
        "provider": {"organization": " ", "url": " ", "extra": 42},
        "documentationUrl": "ftp://docs.example.org",
        "iconUrl": "http://external.example.org/icon.png",
        "securitySchemes": "invalid",
    }
    bad_issues = validate_card(bad_card)
    assert any(i.code == "empty" and i.path == "name" for i in bad_issues)
    assert any(i.code == "empty" and i.path == "description" for i in bad_issues)
    assert any(i.code == "empty" and i.path == "version" for i in bad_issues)
    assert any(i.code == "empty" and i.path == "supportedInterfaces[0].url" for i in bad_issues)
    assert any(
        i.code == "empty" and i.path == "supportedInterfaces[0].protocolBinding" for i in bad_issues
    )
    assert any(
        i.code == "empty" and i.path == "supportedInterfaces[0].protocolVersion" for i in bad_issues
    )
    assert any(i.code == "empty" and i.path == "supportedInterfaces[0].tenant" for i in bad_issues)
    assert any(
        i.code == "unknown_field" and i.path == "supportedInterfaces[0].extra" for i in bad_issues
    )
    assert any(i.code == "type" and i.path == "capabilities.pushNotifications" for i in bad_issues)
    assert any(i.code == "type" and i.path == "capabilities.extendedAgentCard" for i in bad_issues)
    assert any(i.code == "type" and i.path == "capabilities.extensions" for i in bad_issues)
    assert any(i.code == "empty" and i.path == "defaultInputModes[0]" for i in bad_issues)
    assert any(i.code == "type" and i.path == "defaultOutputModes[0]" for i in bad_issues)
    assert any(i.code == "empty" and i.path == "skills[0].id" for i in bad_issues)
    assert any(i.code == "empty" and i.path == "skills[0].name" for i in bad_issues)
    assert any(i.code == "empty" and i.path == "skills[0].description" for i in bad_issues)
    assert any(i.code == "empty" and i.path == "skills[0].tags[0]" for i in bad_issues)
    assert any(i.code == "type" and i.path == "skills[0].tags[1]" for i in bad_issues)
    assert any(i.code == "empty" and i.path == "skills[0].examples[0]" for i in bad_issues)
    assert any(i.code == "type" and i.path == "skills[0].examples[1]" for i in bad_issues)
    assert any(
        i.code == "invalid_media_type" and i.path == "skills[0].inputModes[0]" for i in bad_issues
    )
    assert any(
        i.code == "invalid_media_type" and i.path == "skills[0].outputModes[0]" for i in bad_issues
    )
    assert any(i.code == "type" and i.path == "skills[0].securityRequirements" for i in bad_issues)
    assert any(i.code == "unknown_field" and i.path == "skills[0].extra" for i in bad_issues)
    assert any(i.code == "empty" and i.path == "provider.organization" for i in bad_issues)
    assert any(i.code == "empty" and i.path == "provider.url" for i in bad_issues)
    assert any(i.code == "unknown_field" and i.path == "provider.extra" for i in bad_issues)
    assert any(i.code == "invalid_url" and i.path == "documentationUrl" for i in bad_issues)
    assert any(i.code == "invalid_url" and i.path == "iconUrl" for i in bad_issues)
    assert any(i.code == "type" and i.path == "securitySchemes" for i in bad_issues)


def test_validate_card_missing_and_wrong_types() -> None:
    # Non-dict interface or skill
    card: dict[str, Any] = {
        "name": 123,
        "description": False,
        "version": True,
        "supportedInterfaces": "not-a-list",
        "capabilities": "not-a-dict",
        "defaultInputModes": "not-a-list",
        "defaultOutputModes": "not-a-list",
        "skills": "not-a-list",
        "provider": "not-a-dict",
    }
    issues = validate_card(card)
    assert any(i.path == "name" and i.code == "type" for i in issues)
    assert any(i.path == "description" and i.code == "type" for i in issues)
    assert any(i.path == "version" and i.code == "type" for i in issues)
    assert any(i.path == "supportedInterfaces" and i.code == "type" for i in issues)
    assert any(i.path == "capabilities" and i.code == "type" for i in issues)
    assert any(i.path == "defaultInputModes" and i.code == "type" for i in issues)
    assert any(i.path == "defaultOutputModes" and i.code == "type" for i in issues)
    assert any(i.path == "skills" and i.code == "type" for i in issues)
    assert any(i.path == "provider" and i.code == "type" for i in issues)

    # Interface with non-dict elements and missing fields
    card2: dict[str, Any] = {
        "name": "Name",
        "description": "Desc",
        "version": "1.0.0",
        "supportedInterfaces": [123, {}],
        "capabilities": {},
        "defaultInputModes": [],
        "defaultOutputModes": [],
        "skills": [456, {}],
        "provider": {},
    }
    issues2 = validate_card(card2)
    assert any(i.path == "supportedInterfaces[0]" and i.code == "type" for i in issues2)
    assert any(i.path == "supportedInterfaces[1].url" and i.code == "missing" for i in issues2)
    assert any(
        i.path == "supportedInterfaces[1].protocolBinding" and i.code == "missing" for i in issues2
    )
    assert any(
        i.path == "supportedInterfaces[1].protocolVersion" and i.code == "missing" for i in issues2
    )
    assert any(i.path == "skills[0]" and i.code == "type" for i in issues2)
    assert any(i.path == "skills[1].id" and i.code == "missing" for i in issues2)
    assert any(i.path == "skills[1].name" and i.code == "missing" for i in issues2)
    assert any(i.path == "skills[1].description" and i.code == "missing" for i in issues2)
    assert any(i.path == "skills[1].tags" and i.code == "missing" for i in issues2)
    assert any(i.path == "provider.organization" and i.code == "missing" for i in issues2)
    assert any(i.path == "provider.url" and i.code == "missing" for i in issues2)


def test_local_ipv6_accepted() -> None:
    card = build_card(
        name="Search",
        description="Finds docs",
        version="1.0.0",
        interfaces=[Interface("http://[::1]:8080/a2a", "JSONRPC", "1.0")],
        skills=[Skill("s", "S", "D", ("t",))],
    )
    assert [i for i in validate_card(card) if i.path == "supportedInterfaces[0].url"] == []


def test_well_known_url_errors() -> None:
    with pytest.raises(A2ACardError):
        well_known_url("")
    with pytest.raises(A2ACardError):
        well_known_url("ftp://example.com")
    with pytest.raises(A2ACardError):
        well_known_url("https://" + "a" * 5000)


def test_cli_usage_and_warnings(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # No args
    assert main([]) == 2
    # Unknown cmd
    assert main(["invalid"]) == 2
    # Non-existent file
    assert main(["validate", str(tmp_path / "not_exists.json")]) == 2

    # Only warning yields return code 0
    card = build_card(
        name="Search",
        description="Finds docs",
        version="1.0.0",
        interfaces=[Interface("https://agent.example.com/a2a", "SOAP", "1.0")],
        skills=[Skill("search", "Search", "Search docs", ("docs",))],
    )
    warning_file = tmp_path / "warning.json"
    warning_file.write_text(json.dumps(card), encoding="utf-8")
    ret = main(["validate", str(warning_file)])
    captured = capsys.readouterr()
    assert ret == 0
    assert "warning supportedInterfaces[0].protocolBinding unknown_binding" in captured.out
