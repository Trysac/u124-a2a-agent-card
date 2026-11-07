# Zero-dependency A2A Agent Card Builder and Validator

Status: accepted (generated, pending human review)

## Context

The Agent2Agent (A2A) protocol requires agents to advertise their capabilities, interfaces, skills, and provider details via an Agent Card located at a well-known discovery URL. Agents frequently fail validation in CI due to malformed URLs, invalid MIME types, or missing fields. A lightweight, dependency-free validator with deterministic path-level reporting is required.

## Decision

Implement the builder and validator using standard library primitives (`urllib.parse`, `dataclasses`, `re`, `json`). Validate field existence, types, non-empty string constraints, media types, and local/https URL schemes according to the A2A v1.0.0 specification.

## Consequences

Users can build and validate A2A agent cards without external dependencies. Unknown fields and unrecognized protocol bindings produce non-blocking warnings, while schema violations produce structured path-annotated errors.
