# Architecture

## Purpose

`trysac-a2a-agent-card` is a small, dependency-free Python library: Build and validate A2A protocol Agent Cards against the v1.0.0 field rules, with JSON-path issues, media type and URL checks and the well-known discovery URL

## Shape

```text
caller code --> a2a_agent_card (public API in __init__.py)
                    |
                    +-- pure functions, no I/O, no global state
```

- **Public API**: the names listed in `__all__` of `src/a2a_agent_card/__init__.py`. Anything else is
  internal and may change without a major version.
- **Errors**: invalid input raises built-in exceptions (`ValueError`, `TypeError`) with a clear
  message; the library never prints or exits.
- **Side effects**: none. If a feature needs I/O, isolate it in its own module behind a small
  interface and record the choice in an ADR.

## Quality contract

`scripts/check.py` is the single definition of the gates; `fabrica.json` tells the factory and CI
how to run it. See [TESTING.md](TESTING.md).

## Decisions

Architecture decisions are recorded in [decisions/](decisions/) as numbered ADRs.
