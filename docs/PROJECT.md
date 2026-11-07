# Project record

## Objective

Build and validate A2A protocol Agent Cards against the v1.0.0 field rules, with JSON-path issues, media type and URL checks and the well-known discovery URL

## Scope

- In scope: the public API documented in [README.md](../README.md), typed and tested.
- Out of scope: anything that needs runtime dependencies or I/O without an accepted ADR.

## Timeline

| Date | Event |
|---|---|
| 2026 | Repository created from the factory utility template. |

## Effort metrics

Measured values only; a value that has not been measured stays "pending measurement".

| Metric | Value |
|---|---|
| Tokens (input / output) | 478114 / 16655 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.0980 |

## Factory run u124 (measured from API usage)

| Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|
| generation | gemini-3.8-flash | yes | 4444 | 14030 | 0 | 0 | 0.0280 |
| fix-1 | gemini-3.1-flash-lite | no | 37117 | 1154 | 0 | 75407 | 0.0129 |
| audit | gemini-3.1-flash-lite | no | 50532 | 415 | 0 | 156995 | 0.0172 |
| docs | gemini-3.1-flash-lite | no | 153619 | 1056 | 0 | 0 | 0.0400 |

Total: $0.0980. Prices: Anthropic list prices.
