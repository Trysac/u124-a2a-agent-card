# Architecture

## Overview

`trysac-a2a-agent-card` provides a zero-dependency implementation of the Agent2Agent (A2A) protocol specification v1.0.0 (section 4.4 Agent Discovery Objects and section 8.2 Discovery).

## Components

1. **Data Models (`Interface`, `Skill`, `Capabilities`, `Issue`)**:
   Frozen dataclasses representing the core agent discovery objects defined by the A2A specification.
2. **Builder (`build_card`)**:
   Pure function that maps strongly-typed components into standard A2A agent card dictionary representations.
3. **Validator (`validate_card`)**:
   Deterministic validator that walks card structures, checking required fields, JSON data types, media types according to standard MIME conventions, URL schemes (enforcing `https` except for loopback addresses `localhost`, `127.0.0.1`, and `::1`), duplicate skill IDs, and unknown fields.
   Returns sorted lists of `Issue` records (`error` or `warning`).
4. **Discovery Helper (`well_known_url`)**:
   Derives RFC 8615 well-known discovery URLs (`https://{origin}/.well-known/agent-card.json`).
5. **Command Line Interface (`__main__.py`)**:
   CLI entry point for running card validation in CI and automated pipelines.
