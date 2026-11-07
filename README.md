# a2a-agent-card

[![PyPI version](https://img.shields.io/pypi/v/trysac-a2a-agent-card)](https://pypi.org/project/trysac-a2a-agent-card/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-a2a-agent-card)](LICENSE)
[![CI](https://github.com/Trysac/u124-a2a-agent-card/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u124-a2a-agent-card/actions/workflows/ci.yml)

Build and validate A2A protocol Agent Cards against the v1.0.0 field rules, with JSON-path issues, media type and URL checks and the well-known discovery URL

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-a2a-agent-card
# or
uv add trysac-a2a-agent-card
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import a2a_agent_card

# normalize() trims surrounding whitespace and lower-cases the text.
print(a2a_agent_card.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    a2a_agent_card.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
