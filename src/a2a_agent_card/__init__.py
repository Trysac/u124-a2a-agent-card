"""A2A protocol Agent Card builder and validator (v1.0.0 rules)."""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import urlparse

__all__ = [
    "KNOWN_BINDINGS",
    "A2ACardError",
    "Capabilities",
    "Interface",
    "Issue",
    "Skill",
    "__version__",
    "build_card",
    "validate_card",
    "well_known_url",
]

__version__ = "0.1.0"

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Rules from A2A specification v1.0.0 (a2a-protocol.org, checked 2026-11-06)
KNOWN_BINDINGS: tuple[str, ...] = ("JSONRPC", "GRPC", "HTTP+JSON")

MAX_INPUT_BYTES: int = 1_048_576
MAX_DEPTH: int = 32

_MEDIA_TYPE_REGEX = re.compile(
    r"^[a-z0-9][a-z0-9!#$&^_.+-]*/[a-z0-9][a-z0-9!#$&^_.+-]*$", re.IGNORECASE
)
_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


class A2ACardError(Exception):
    """Base typed error for a2a_agent_card operations."""

    def __init__(self, code: Literal["invalid_url", "invalid_input"], message: str = "") -> None:
        self.code: Literal["invalid_url", "invalid_input"] = code
        safe_msg = message[:200] if message else code
        super().__init__(safe_msg)


@dataclass(frozen=True)
class Interface:
    """AgentInterface per A2A section 4.4.6."""

    url: str
    protocol_binding: str
    protocol_version: str
    tenant: str | None = None


@dataclass(frozen=True)
class Skill:
    """AgentSkill per A2A section 4.4.5."""

    id: str
    name: str
    description: str
    tags: tuple[str, ...]
    examples: tuple[str, ...] = ()
    input_modes: tuple[str, ...] | None = None
    output_modes: tuple[str, ...] | None = None


@dataclass(frozen=True)
class Capabilities:
    """AgentCapabilities per A2A section 4.4.3."""

    streaming: bool | None = None
    push_notifications: bool | None = None
    extended_agent_card: bool | None = None


@dataclass(frozen=True)
class Issue:
    """Validation issue with path, code, and severity."""

    path: str
    code: str
    severity: Literal["error", "warning"]


def well_known_url(base_url: str) -> str:
    """Return the well-known agent card URL for base_url (RFC 8615 origin discovery)."""
    if not isinstance(base_url, str) or not base_url.strip():
        raise A2ACardError("invalid_url", "URL must not be empty")
    if len(base_url) > 4096:
        raise A2ACardError("invalid_url", "URL exceeds maximum length")
    parsed = urlparse(base_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise A2ACardError("invalid_url", f"Invalid base URL: {base_url[:50]}")
    # Check local or https rule per A2A Discovery specification
    host = (parsed.hostname or "").lower()
    if not host:
        raise A2ACardError("invalid_url", "URL host missing")
    port_str = f":{parsed.port}" if parsed.port is not None else ""
    origin = f"{parsed.scheme}://{host}{port_str}"
    return f"{origin}/.well-known/agent-card.json"


def build_card(
    *,
    name: str,
    description: str,
    version: str,
    interfaces: Sequence[Interface],
    skills: Sequence[Skill],
    capabilities: Capabilities | None = None,
    default_input_modes: Sequence[str] = ("text/plain",),
    default_output_modes: Sequence[str] = ("text/plain",),
    provider: tuple[str, str] | None = None,
    documentation_url: str | None = None,
    icon_url: str | None = None,
) -> dict[str, Any]:
    """Build a standard A2A agent card dictionary."""
    if not skills:
        raise A2ACardError("invalid_input", "At least one skill is required in build_card")
    if not interfaces:
        raise A2ACardError("invalid_input", "At least one interface is required in build_card")
    if not isinstance(name, str) or not name.strip():
        raise A2ACardError("invalid_input", "Name must be a non-empty string")

    card: dict[str, Any] = {
        "capabilities": {},
        "defaultInputModes": list(default_input_modes),
        "defaultOutputModes": list(default_output_modes),
        "description": description,
        "name": name,
        "skills": [],
        "supportedInterfaces": [],
        "version": version,
    }

    if capabilities is None:
        capabilities = Capabilities()

    caps: dict[str, Any] = {}
    if capabilities.streaming is not None:
        caps["streaming"] = capabilities.streaming
    if capabilities.push_notifications is not None:
        caps["pushNotifications"] = capabilities.push_notifications
    if capabilities.extended_agent_card is not None:
        caps["extendedAgentCard"] = capabilities.extended_agent_card
    card["capabilities"] = caps

    for iface in interfaces:
        iface_dict: dict[str, Any] = {
            "protocolBinding": iface.protocol_binding,
            "protocolVersion": iface.protocol_version,
            "url": iface.url,
        }
        if iface.tenant is not None:
            iface_dict["tenant"] = iface.tenant
        card["supportedInterfaces"].append(iface_dict)

    for skill in skills:
        sk: dict[str, Any] = {
            "description": skill.description,
            "id": skill.id,
            "name": skill.name,
            "tags": list(skill.tags),
        }
        if skill.examples:
            sk["examples"] = list(skill.examples)
        if skill.input_modes is not None:
            sk["inputModes"] = list(skill.input_modes)
        if skill.output_modes is not None:
            sk["outputModes"] = list(skill.output_modes)
        card["skills"].append(sk)

    if provider is not None:
        card["provider"] = {"organization": provider[0], "url": provider[1]}
    if documentation_url is not None:
        card["documentationUrl"] = documentation_url
    if icon_url is not None:
        card["iconUrl"] = icon_url

    return card


def _is_strict_bool(val: Any) -> bool:
    return isinstance(val, bool)


def _is_strict_str(val: Any) -> bool:
    return isinstance(val, str) and not isinstance(val, bool)


def _is_strict_list(val: Any) -> bool:
    return isinstance(val, list)


def _is_strict_dict(val: Any) -> bool:
    return isinstance(val, dict)


def _validate_url(path: str, url_val: Any, issues: list[Issue]) -> None:
    if not _is_strict_str(url_val):
        issues.append(Issue(path, "type", "error"))
        return
    if not url_val.strip():
        issues.append(Issue(path, "empty", "error"))
        return
    try:
        parsed = urlparse(url_val)
    except Exception:
        issues.append(Issue(path, "invalid_url", "error"))
        return

    host = (parsed.hostname or "").lower()
    if not parsed.scheme or not host:
        issues.append(Issue(path, "invalid_url", "error"))
        return

    if parsed.scheme == "https":
        return
    if parsed.scheme == "http":
        if host in _LOCAL_HOSTS:
            return
        issues.append(Issue(path, "invalid_url", "error"))
        return
    issues.append(Issue(path, "invalid_url", "error"))


def _validate_media_type(path: str, val: Any, issues: list[Issue]) -> None:
    if not _is_strict_str(val):
        issues.append(Issue(path, "type", "error"))
        return
    if not val.strip():
        issues.append(Issue(path, "empty", "error"))
        return
    if not _MEDIA_TYPE_REGEX.match(val):
        issues.append(Issue(path, "invalid_media_type", "error"))


def validate_card(card: Mapping[str, Any]) -> list[Issue]:
    """Validate an A2A Agent Card against the v1.0.0 specification rules."""
    issues: list[Issue] = []

    if not isinstance(card, (dict, Mapping)):
        return [Issue("", "type", "error")]

    known_top_level = {
        "name",
        "description",
        "supportedInterfaces",
        "version",
        "capabilities",
        "defaultInputModes",
        "defaultOutputModes",
        "skills",
        "provider",
        "documentationUrl",
        "securitySchemes",
        "securityRequirements",
        "signatures",
        "iconUrl",
    }

    for key in card:
        if key not in known_top_level:
            issues.append(Issue(key, "unknown_field", "warning"))

    required_top_strings = ("name", "description", "version")
    for field in required_top_strings:
        if field not in card:
            issues.append(Issue(field, "missing", "error"))
        else:
            val = card[field]
            if not _is_strict_str(val):
                issues.append(Issue(field, "type", "error"))
            elif not val.strip():
                issues.append(Issue(field, "empty", "error"))

    # supportedInterfaces
    if "supportedInterfaces" not in card:
        issues.append(Issue("supportedInterfaces", "missing", "error"))
    else:
        val = card["supportedInterfaces"]
        if not _is_strict_list(val):
            issues.append(Issue("supportedInterfaces", "type", "error"))
        else:
            for i, item in enumerate(val):
                ipath = f"supportedInterfaces[{i}]"
                if not _is_strict_dict(item):
                    issues.append(Issue(ipath, "type", "error"))
                    continue
                known_iface_fields = {"url", "protocolBinding", "protocolVersion", "tenant"}
                for k in item:
                    if k not in known_iface_fields:
                        issues.append(Issue(f"{ipath}.{k}", "unknown_field", "warning"))
                # url
                if "url" not in item:
                    issues.append(Issue(f"{ipath}.url", "missing", "error"))
                else:
                    _validate_url(f"{ipath}.url", item["url"], issues)
                # protocolBinding
                if "protocolBinding" not in item:
                    issues.append(Issue(f"{ipath}.protocolBinding", "missing", "error"))
                else:
                    pb = item["protocolBinding"]
                    if not _is_strict_str(pb):
                        issues.append(Issue(f"{ipath}.protocolBinding", "type", "error"))
                    elif not pb.strip():
                        issues.append(Issue(f"{ipath}.protocolBinding", "empty", "error"))
                    elif pb not in KNOWN_BINDINGS:
                        issues.append(
                            Issue(f"{ipath}.protocolBinding", "unknown_binding", "warning")
                        )
                # protocolVersion
                if "protocolVersion" not in item:
                    issues.append(Issue(f"{ipath}.protocolVersion", "missing", "error"))
                else:
                    pv = item["protocolVersion"]
                    if not _is_strict_str(pv):
                        issues.append(Issue(f"{ipath}.protocolVersion", "type", "error"))
                    elif not pv.strip():
                        issues.append(Issue(f"{ipath}.protocolVersion", "empty", "error"))
                # tenant (optional)
                if "tenant" in item:
                    tn = item["tenant"]
                    if not _is_strict_str(tn):
                        issues.append(Issue(f"{ipath}.tenant", "type", "error"))
                    elif not tn.strip():
                        issues.append(Issue(f"{ipath}.tenant", "empty", "error"))

    # capabilities
    if "capabilities" not in card:
        issues.append(Issue("capabilities", "missing", "error"))
    else:
        caps = card["capabilities"]
        if not _is_strict_dict(caps):
            issues.append(Issue("capabilities", "type", "error"))
        else:
            known_caps = {"streaming", "pushNotifications", "extendedAgentCard", "extensions"}
            for k in caps:
                if k not in known_caps:
                    issues.append(Issue(f"capabilities.{k}", "unknown_field", "warning"))
            for bool_field in ("streaming", "pushNotifications", "extendedAgentCard"):
                if (
                    bool_field in caps
                    and caps[bool_field] is not None
                    and not _is_strict_bool(caps[bool_field])
                ):
                    issues.append(Issue(f"capabilities.{bool_field}", "type", "error"))
            if (
                "extensions" in caps
                and caps["extensions"] is not None
                and not _is_strict_list(caps["extensions"])
            ):
                issues.append(Issue("capabilities.extensions", "type", "error"))

    # defaultInputModes
    if "defaultInputModes" not in card:
        issues.append(Issue("defaultInputModes", "missing", "error"))
    else:
        dim = card["defaultInputModes"]
        if not _is_strict_list(dim):
            issues.append(Issue("defaultInputModes", "type", "error"))
        else:
            for i, mode in enumerate(dim):
                _validate_media_type(f"defaultInputModes[{i}]", mode, issues)

    # defaultOutputModes
    if "defaultOutputModes" not in card:
        issues.append(Issue("defaultOutputModes", "missing", "error"))
    else:
        dom = card["defaultOutputModes"]
        if not _is_strict_list(dom):
            issues.append(Issue("defaultOutputModes", "type", "error"))
        else:
            for i, mode in enumerate(dom):
                _validate_media_type(f"defaultOutputModes[{i}]", mode, issues)

    # skills
    if "skills" not in card:
        issues.append(Issue("skills", "missing", "error"))
    else:
        sk_val = card["skills"]
        if not _is_strict_list(sk_val):
            issues.append(Issue("skills", "type", "error"))
        else:
            seen_skill_ids: set[str] = set()
            for i, skill in enumerate(sk_val):
                spath = f"skills[{i}]"
                if not _is_strict_dict(skill):
                    issues.append(Issue(spath, "type", "error"))
                    continue
                known_skill_fields = {
                    "id",
                    "name",
                    "description",
                    "tags",
                    "examples",
                    "inputModes",
                    "outputModes",
                    "securityRequirements",
                }
                for k in skill:
                    if k not in known_skill_fields:
                        issues.append(Issue(f"{spath}.{k}", "unknown_field", "warning"))

                # id
                if "id" not in skill:
                    issues.append(Issue(f"{spath}.id", "missing", "error"))
                else:
                    sid = skill["id"]
                    if not _is_strict_str(sid):
                        issues.append(Issue(f"{spath}.id", "type", "error"))
                    elif not sid.strip():
                        issues.append(Issue(f"{spath}.id", "empty", "error"))
                    else:
                        if sid in seen_skill_ids:
                            issues.append(Issue(f"{spath}.id", "duplicate_skill_id", "error"))
                        seen_skill_ids.add(sid)

                # name
                if "name" not in skill:
                    issues.append(Issue(f"{spath}.name", "missing", "error"))
                else:
                    sname = skill["name"]
                    if not _is_strict_str(sname):
                        issues.append(Issue(f"{spath}.name", "type", "error"))
                    elif not sname.strip():
                        issues.append(Issue(f"{spath}.name", "empty", "error"))

                # description
                if "description" not in skill:
                    issues.append(Issue(f"{spath}.description", "missing", "error"))
                else:
                    sdesc = skill["description"]
                    if not _is_strict_str(sdesc):
                        issues.append(Issue(f"{spath}.description", "type", "error"))
                    elif not sdesc.strip():
                        issues.append(Issue(f"{spath}.description", "empty", "error"))

                # tags
                if "tags" not in skill:
                    issues.append(Issue(f"{spath}.tags", "missing", "error"))
                else:
                    stags = skill["tags"]
                    if not _is_strict_list(stags):
                        issues.append(Issue(f"{spath}.tags", "type", "error"))
                    else:
                        for j, tag in enumerate(stags):
                            if not _is_strict_str(tag):
                                issues.append(Issue(f"{spath}.tags[{j}]", "type", "error"))
                            elif not tag.strip():
                                issues.append(Issue(f"{spath}.tags[{j}]", "empty", "error"))

                # examples
                if "examples" in skill:
                    sexamples = skill["examples"]
                    if not _is_strict_list(sexamples):
                        issues.append(Issue(f"{spath}.examples", "type", "error"))
                    else:
                        for j, ex in enumerate(sexamples):
                            if not _is_strict_str(ex):
                                issues.append(Issue(f"{spath}.examples[{j}]", "type", "error"))
                            elif not ex.strip():
                                issues.append(Issue(f"{spath}.examples[{j}]", "empty", "error"))

                # inputModes
                if "inputModes" in skill:
                    sim = skill["inputModes"]
                    if not _is_strict_list(sim):
                        issues.append(Issue(f"{spath}.inputModes", "type", "error"))
                    else:
                        for j, mode in enumerate(sim):
                            _validate_media_type(f"{spath}.inputModes[{j}]", mode, issues)

                # outputModes
                if "outputModes" in skill:
                    som = skill["outputModes"]
                    if not _is_strict_list(som):
                        issues.append(Issue(f"{spath}.outputModes", "type", "error"))
                    else:
                        for j, mode in enumerate(som):
                            _validate_media_type(f"{spath}.outputModes[{j}]", mode, issues)

                # securityRequirements
                if "securityRequirements" in skill:
                    sec_req = skill["securityRequirements"]
                    if not _is_strict_list(sec_req) and not _is_strict_dict(sec_req):
                        issues.append(Issue(f"{spath}.securityRequirements", "type", "error"))

    # provider
    if "provider" in card:
        provider = card["provider"]
        if not _is_strict_dict(provider):
            issues.append(Issue("provider", "type", "error"))
        else:
            known_provider = {"url", "organization"}
            for k in provider:
                if k not in known_provider:
                    issues.append(Issue(f"provider.{k}", "unknown_field", "warning"))
            if "organization" not in provider:
                issues.append(Issue("provider.organization", "missing", "error"))
            else:
                org = provider["organization"]
                if not _is_strict_str(org):
                    issues.append(Issue("provider.organization", "type", "error"))
                elif not org.strip():
                    issues.append(Issue("provider.organization", "empty", "error"))
            if "url" not in provider:
                issues.append(Issue("provider.url", "missing", "error"))
            else:
                _validate_url("provider.url", provider["url"], issues)

    # documentationUrl
    if "documentationUrl" in card:
        _validate_url("documentationUrl", card["documentationUrl"], issues)

    # iconUrl
    if "iconUrl" in card:
        _validate_url("iconUrl", card["iconUrl"], issues)

    # securitySchemes, securityRequirements, signatures
    for sec_field in ("securitySchemes", "securityRequirements", "signatures"):
        if sec_field in card:
            val = card[sec_field]
            if not _is_strict_dict(val) and not _is_strict_list(val):
                issues.append(Issue(sec_field, "type", "error"))

    # Sort issues by path, then code
    issues.sort(key=lambda x: (x.path, x.code))
    return issues
